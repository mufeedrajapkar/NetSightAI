"""
test_phase5a_bot_pipeline.py
----------------------------
CN_AI Phase 5A — Bot-to-AI end-to-end integration test.

Pipeline under test:
    Bot logic -> Flask test client -> synthetic packet synthesis
    -> FlowProcessor (FlowTracker + SessionTracker + extract_features)
    -> AIBridge.predict()
    -> predicted label + probability estimates

Design choices
--------------
* Flask's built-in test client (werkzeug) is used instead of a live TCP server.
  This removes port-binding, subprocess management, and timing fragility while
  still exercising the *exact same* Flask application that runs in production
  (bots/test_server.py). No live network capture is performed.

* Synthetic packet_data dicts are constructed from HTTP request/response
  metadata (URL length -> request size, response body length -> response size,
  monotonically increasing timestamps). The 5-tuple is fixed to loopback
  (127.0.0.1:ephemeral_port <-> 127.0.0.1:5000) with protocol TCP, matching
  the model's training distribution. This is the smallest faithful
  representation of bot traffic that the existing CN stack can process.

* All three bot tiers are exercised. The expected ground-truth label is
  "Bot" for all three; the model's *actual* prediction may differ because
  the model was trained on synthetic sessions and this test generates short
  in-process flows. The test explicitly distinguishes expected vs. predicted.

* No files are written, no model is retrained, no changes are made to
  existing source files, and no live sockets are opened.
"""

import os
import sys
import random
import importlib.util

import pytest

# ---------------------------------------------------------------------------
# Repo-root imports: works when pytest is run from d:\CN_AI
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from CN.agent.flow.flow_processor import FlowProcessor
from CN.agent.ai_bridge import AIBridge


# ---------------------------------------------------------------------------
# Load Flask app from bots/test_server.py without executing __main__
# ---------------------------------------------------------------------------

_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "bots", "test_server.py")
)


def _load_flask_app():
    """Load bots/test_server.py as a module and return its Flask app object."""
    spec = importlib.util.spec_from_file_location("_test_server", _SERVER_PATH)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app


# ---------------------------------------------------------------------------
# Packet synthesis helpers
# ---------------------------------------------------------------------------

_CLIENT_IP   = "127.0.0.1"
_SERVER_IP   = "127.0.0.1"
_SERVER_PORT = 5000
_BASE_HDR    = 54    # Ethernet + IP + TCP header bytes (approximate)


def _make_packet(t, src_ip, src_port, dst_ip, dst_port,
                 payload_bytes, is_syn=False, is_ack=False,
                 is_fin=False, is_rst=False, seq=None):
    """Return a packet_data dict in the shape FlowTracker.add_packet() expects."""
    return {
        "time":        float(t),
        "src_ip":      src_ip,
        "src_port":    src_port,
        "dst_ip":      dst_ip,
        "dst_port":    dst_port,
        "protocol":    "TCP",
        "packet_size": _BASE_HDR + max(0, int(payload_bytes)),
        "is_syn":      is_syn,
        "is_ack":      is_ack,
        "is_fin":      is_fin,
        "is_rst":      is_rst,
        "seq":         seq,
    }


def _synthesize_exchange(client_port, t_req, t_resp,
                         req_bytes, resp_bytes, seq_req, seq_resp):
    """
    Return two packet_data dicts representing one HTTP request/response
    exchange over an established TCP connection (no handshake packets).
    """
    return [
        # Client -> Server: HTTP request data segment
        _make_packet(t_req,  _CLIENT_IP, client_port,
                     _SERVER_IP, _SERVER_PORT,
                     req_bytes, is_ack=True, seq=seq_req),
        # Server -> Client: HTTP response data segment
        _make_packet(t_resp, _SERVER_IP, _SERVER_PORT,
                     _CLIENT_IP, client_port,
                     resp_bytes, is_ack=True, seq=seq_resp),
    ]


def _tcp_handshake(client_port, t0):
    """Return the three SYN / SYN-ACK / ACK packets for a fresh TCP connection."""
    return [
        _make_packet(t0,         _CLIENT_IP, client_port,
                     _SERVER_IP, _SERVER_PORT,
                     0, is_syn=True,  is_ack=False, seq=1000),
        _make_packet(t0 + 0.001, _SERVER_IP, _SERVER_PORT,
                     _CLIENT_IP, client_port,
                     0, is_syn=True,  is_ack=True,  seq=5000),
        _make_packet(t0 + 0.002, _CLIENT_IP, client_port,
                     _SERVER_IP, _SERVER_PORT,
                     0, is_syn=False, is_ack=True,  seq=1001),
    ]


def _tcp_teardown(client_port, t_fin):
    """Return FIN-ACK / ACK packets for an orderly TCP close."""
    return [
        _make_packet(t_fin,         _CLIENT_IP, client_port,
                     _SERVER_IP, _SERVER_PORT,
                     0, is_fin=True, is_ack=True, seq=9000),
        _make_packet(t_fin + 0.001, _SERVER_IP, _SERVER_PORT,
                     _CLIENT_IP, client_port,
                     0, is_ack=True, seq=5001),
    ]


# ---------------------------------------------------------------------------
# BotTrafficPipeline
# ---------------------------------------------------------------------------

class BotTrafficPipeline:
    """
    Runs one bot tier's traffic pattern against the Flask test client,
    synthesises TCP packet_data dicts from HTTP metadata, feeds them through
    FlowProcessor, and classifies the resulting session via AIBridge.

    Parameters
    ----------
    flask_app : Flask application object (from bots/test_server.py)
    bot_label : Ground-truth label string (e.g. "bot_tier1")
    device_id : Device identifier forwarded to FlowProcessor
    """

    def __init__(self, flask_app, bot_label, device_id="PC01"):
        self.flask_app  = flask_app
        self.bot_label  = bot_label
        self.device_id  = device_id
        # csv_file=os.devnull suppresses CSV writes; FlowProcessor is otherwise
        # identical to production use.
        self._processor = FlowProcessor(
            device_id=device_id,
            label=bot_label,
            bot_tier=bot_label,
            csv_file=os.devnull,
        )
        self._bridge = AIBridge()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _issue_request(self, client, url, method="GET", json_body=None,
                       t_base=0.0, client_port=50000,
                       seq_req=2000, seq_resp=6000):
        """
        Send one request via the Flask test client and build the corresponding
        packet exchange. Returns (flask_response, list_of_packet_dicts).
        """
        if method == "GET":
            resp = client.get(url)
        else:
            resp = client.post(url, json=json_body)

        req_bytes  = len(url) + (len(str(json_body)) if json_body else 0) + 200
        resp_bytes = len(resp.data)

        pkts = _synthesize_exchange(
            client_port=client_port,
            t_req=t_base,
            t_resp=t_base + 0.01,
            req_bytes=req_bytes,
            resp_bytes=resp_bytes,
            seq_req=seq_req,
            seq_resp=seq_resp,
        )
        return resp, pkts

    def _process_and_classify(self, packets):
        """
        Feed all packets through FlowProcessor one at a time and classify the
        final accumulated session via AIBridge.

        Returns the AIBridge prediction result dict, augmented with:
          - "expected_label"   : ground-truth bot label
          - "packet_count"     : total packets absorbed by FlowTracker
          - "session_duration" : session duration in seconds (from features)
        """
        last_features = None
        for pkt in packets:
            last_features = self._processor.process_packet(pkt)

        if last_features is None:
            raise RuntimeError("No features produced — packet list was empty.")

        result = self._bridge.predict(last_features)
        result["expected_label"]   = self.bot_label
        result["packet_count"]     = last_features.get("packet_count", 0)
        result["session_duration"] = last_features.get("session_duration", 0.0)
        return result

    # ------------------------------------------------------------------
    # Bot tier runners
    # ------------------------------------------------------------------

    def run_tier1(self, n_requests=8, interval=0.5):
        """
        Tier 1 (Naive): fixed-interval GET / requests on a single connection.
        """
        client_port = 50001
        t0 = 0.0
        all_pkts = list(_tcp_handshake(client_port, t0))
        t_cursor = t0 + 0.005

        with self.flask_app.test_client() as client:
            for i in range(n_requests):
                _, pkts = self._issue_request(
                    client, "/",
                    t_base=t_cursor,
                    client_port=client_port,
                    seq_req=2000  + i * 500,
                    seq_resp=6000 + i * 1000,
                )
                all_pkts.extend(pkts)
                t_cursor += interval

        all_pkts.extend(_tcp_teardown(client_port, t_cursor))
        return self._process_and_classify(all_pkts)

    def run_tier2(self, n_requests=8):
        """
        Tier 2 (Jittered): random-interval GET /search?... requests.
        """
        queries = ["network", "packet", "security", "ai", "classifier"]
        client_port = 50002
        t0 = 0.0
        all_pkts = list(_tcp_handshake(client_port, t0))
        t_cursor = t0 + 0.005
        rng = random.Random(42)   # seeded for reproducibility

        with self.flask_app.test_client() as client:
            for i in range(n_requests):
                q   = rng.choice(queries)
                ref = rng.randint(1, 500)
                url = "/search?q={q}&ref={ref}".format(q=q, ref=ref)
                _, pkts = self._issue_request(
                    client, url,
                    t_base=t_cursor,
                    client_port=client_port,
                    seq_req=2000  + i * 500,
                    seq_resp=6000 + i * 1000,
                )
                all_pkts.extend(pkts)
                t_cursor += rng.uniform(0.2, 2.0)

        all_pkts.extend(_tcp_teardown(client_port, t_cursor))
        return self._process_and_classify(all_pkts)

    def run_tier3(self, n_sessions=2):
        """
        Tier 3 (Mimicking): multi-step browsing (Home -> Search -> Product
        -> Login) with variable pauses between steps.
        """
        endpoints = [
            ("/",              "GET",  None),
            ("/search?q=ai",   "GET",  None),
            ("/product/101",   "GET",  None),
            ("/login",         "POST", {"username": "testuser", "password": "pass"}),
        ]
        client_port = 50003
        t0 = 0.0
        all_pkts = list(_tcp_handshake(client_port, t0))
        t_cursor = t0 + 0.005
        rng = random.Random(7)
        step_idx = 0

        with self.flask_app.test_client() as client:
            for _ in range(n_sessions):
                for url, method, body in endpoints:
                    _, pkts = self._issue_request(
                        client, url, method=method, json_body=body,
                        t_base=t_cursor,
                        client_port=client_port,
                        seq_req=2000  + step_idx * 500,
                        seq_resp=6000 + step_idx * 1000,
                    )
                    all_pkts.extend(pkts)
                    step_idx += 1
                    pause = rng.uniform(0.5, 3.0)
                    if rng.random() < 0.05:
                        pause += rng.uniform(5.0, 15.0)
                    t_cursor += pause

        all_pkts.extend(_tcp_teardown(client_port, t_cursor))
        return self._process_and_classify(all_pkts)


# ---------------------------------------------------------------------------
# Pytest fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def flask_app():
    """Load the Flask test server app once per module (no live socket)."""
    app = _load_flask_app()
    app.config["TESTING"] = True
    return app


# ---------------------------------------------------------------------------
# Helper: assert AIBridge result structure
# ---------------------------------------------------------------------------

def _assert_result_structure(result):
    """Assert that an AIBridge prediction result has the required shape."""
    assert isinstance(result, dict), "Result must be a dict."
    required = {
        "prediction", "probability_estimates", "model_type",
        "features_used", "metadata", "expected_label",
        "packet_count", "session_duration",
    }
    for key in required:
        assert key in result, "Missing key in result: '{k}'".format(k=key)

    assert result["prediction"] in {"Bot", "Human", "Suspicious"}, (
        "Unexpected prediction: {p!r}".format(p=result["prediction"])
    )
    assert isinstance(result["probability_estimates"], dict)
    assert all(isinstance(v, float) for v in result["probability_estimates"].values())
    assert len(result["features_used"]) == 9
    assert result["packet_count"] > 0


# ---------------------------------------------------------------------------
# Helper: pretty-print prediction summary
# ---------------------------------------------------------------------------

def _print_result(tier_name, result):
    """Print a formatted prediction summary (visible with pytest -s)."""
    sep = "=" * 62
    match = ("MATCH"
             if result["prediction"].lower().startswith("bot")
             else "MISMATCH (model uncertainty)")
    print("\n" + sep)
    print("  {name} - AI Classification Result".format(name=tier_name))
    print(sep)
    print("  Expected label    : {e}".format(e=result["expected_label"]))
    print("  Predicted label   : {p}  [{m}]".format(
        p=result["prediction"], m=match))
    print("  Model type        : {t}".format(t=result["model_type"]))
    print("  Packets processed : {c}".format(c=result["packet_count"]))
    print("  Session duration  : {d:.4f}s".format(d=result["session_duration"]))
    print()
    print("  Probability estimates:")
    for cls, prob in sorted(result["probability_estimates"].items(),
                            key=lambda x: -x[1]):
        bar = "#" * int(prob * 30)
        print("    {c:<12} {p:.6f}  {b}".format(c=cls, p=prob, b=bar))
    print()
    print("  Features used (9 contract fields):")
    for k, v in result["features_used"].items():
        print("    {k:<26} {v}".format(k=k, v=v))
    print(sep)


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestPhase5ABotPipeline:
    """
    Phase 5A integration tests: Bot traffic -> CN -> AI pipeline.

    All three bot tiers are exercised through the Flask test client.
    Tests assert *structural* correctness; they intentionally do NOT assert
    a specific prediction class because the Logistic Regression model was
    trained on synthetic data and its boundary may not align perfectly with
    these short in-process flows.  Both "expected_label" (ground truth) and
    "prediction" (model output) are reported so any mismatch is visible.
    """

    # ------------------------------------------------------------------ Tier 1

    def test_tier1_pipeline_produces_valid_result(self, flask_app):
        """TC-P5A-01: Tier 1 (naive) bot produces a structurally valid AI result."""
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier1")
        result   = pipeline.run_tier1(n_requests=8, interval=0.5)
        _assert_result_structure(result)
        _print_result("Tier 1 (Naive)", result)

    def test_tier1_probabilities_sum_to_one(self, flask_app):
        """TC-P5A-02: Probability estimates from Tier 1 sum to approximately 1.0."""
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier1")
        result   = pipeline.run_tier1(n_requests=8, interval=0.5)
        total = sum(result["probability_estimates"].values())
        assert abs(total - 1.0) < 1e-4, (
            "Probabilities do not sum to 1.0: {p}".format(
                p=result["probability_estimates"])
        )

    def test_tier1_metadata_not_in_features_used(self, flask_app):
        """TC-P5A-03: Metadata fields must NOT appear in features_used."""
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier1")
        result   = pipeline.run_tier1(n_requests=8, interval=0.5)
        for forbidden in ("label", "device_id", "bot_tier",
                          "packet_count", "session_id"):
            assert forbidden not in result["features_used"], (
                "Metadata field '{f}' leaked into features_used.".format(
                    f=forbidden)
            )

    # ------------------------------------------------------------------ Tier 2

    def test_tier2_pipeline_produces_valid_result(self, flask_app):
        """TC-P5A-04: Tier 2 (jittered) bot produces a structurally valid AI result."""
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier2")
        result   = pipeline.run_tier2(n_requests=8)
        _assert_result_structure(result)
        _print_result("Tier 2 (Jittered)", result)

    def test_tier2_all_classes_have_probability(self, flask_app):
        """TC-P5A-05: All three model classes appear in probability estimates."""
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier2")
        result   = pipeline.run_tier2(n_requests=8)
        assert set(result["probability_estimates"].keys()) == {
            "Bot", "Human", "Suspicious"
        }

    def test_tier2_features_used_has_exactly_9_keys(self, flask_app):
        """TC-P5A-06: Exactly 9 contract features are passed to the model."""
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier2")
        result   = pipeline.run_tier2(n_requests=8)
        assert len(result["features_used"]) == 9, (
            "Expected 9 contract features; got {n}: {k}".format(
                n=len(result["features_used"]),
                k=list(result["features_used"].keys()))
        )

    # ------------------------------------------------------------------ Tier 3

    def test_tier3_pipeline_produces_valid_result(self, flask_app):
        """TC-P5A-07: Tier 3 (mimicking) bot produces a structurally valid AI result."""
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier3")
        result   = pipeline.run_tier3(n_sessions=2)
        _assert_result_structure(result)
        _print_result("Tier 3 (Mimicking)", result)

    def test_tier3_session_has_meaningful_duration(self, flask_app):
        """TC-P5A-08: Tier 3 session duration must be positive (multi-step flow)."""
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier3")
        result   = pipeline.run_tier3(n_sessions=2)
        assert result["session_duration"] > 0.0, (
            "Expected positive session duration for multi-step Tier 3 flow."
        )

    def test_tier3_packet_count_reflects_all_exchanges(self, flask_app):
        """
        TC-P5A-09: Packet count must reflect the full simulated traffic volume.

        Minimum: 3 (handshake) + 2*n_sessions*4 (data) + 2 (teardown) = 21
        """
        pipeline = BotTrafficPipeline(flask_app, bot_label="bot_tier3")
        result   = pipeline.run_tier3(n_sessions=2)
        assert result["packet_count"] >= 21, (
            "Packet count {c} is below expected minimum of 21.".format(
                c=result["packet_count"])
        )

    # ------------------------------------------------------------------ Cross-tier

    def test_expected_vs_predicted_labels_are_reported(self, flask_app):
        """
        TC-P5A-10: Each tier result must carry both 'expected_label' (ground
        truth) and 'prediction' (model output).  They MAY differ.
        """
        cases = [
            ("bot_tier1", "run_tier1", {"n_requests": 8, "interval": 0.5}),
            ("bot_tier2", "run_tier2", {"n_requests": 8}),
            ("bot_tier3", "run_tier3", {"n_sessions": 2}),
        ]
        for bot_label, method, kwargs in cases:
            pipeline = BotTrafficPipeline(flask_app, bot_label=bot_label)
            result   = getattr(pipeline, method)(**kwargs)
            assert "expected_label" in result, "Missing 'expected_label' key."
            assert "prediction"     in result, "Missing 'prediction' key."
            assert result["expected_label"], "expected_label must be non-empty."
            assert result["prediction"],     "prediction must be non-empty."
