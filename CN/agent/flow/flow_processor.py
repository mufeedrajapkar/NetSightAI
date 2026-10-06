import os
import requests
from typing import Optional

from CN.agent.flow.flow_tracker import FlowTracker
from CN.agent.session.session_tracker import SessionTracker
from CN.agent.features import extract_features
from CN.agent.label_manager import LabelManager
from CN.agent.csv_writer import save_to_csv


def _load_default_api_key() -> str:
    """Retrieve API key from environment variable or fallback."""
    key = os.environ.get("SENTINELNET_API_KEY")
    if key and key.strip():
        return key.strip()

    # Search for .env in repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    env_file = os.path.join(repo_root, ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("SENTINELNET_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    return "sentinelnet-secret-key-change-me"


class FlowProcessor:

    def __init__(
        self,
        device_id: str = "PC01",
        label: str = "Human",
        bot_tier: str = "None",
        csv_file: str = "sentinelnet_dataset.csv",
        server_url: Optional[str] = None,
        api_key: Optional[str] = None,
        push_to_server: bool = False,
        write_local_csv: bool = True,
    ):
        self.device_id = device_id
        self.label = label
        self.bot_tier = bot_tier
        self.tracker = FlowTracker()
        self.session_tracker = SessionTracker(
            timeout=5,
            device_id=device_id
        )

        self.label_manager = LabelManager(
            device_id=device_id,
            label=label,
            bot_tier=bot_tier
        )

        self.csv_file = csv_file

        # Network push configuration
        resolved_server = server_url or os.environ.get("SENTINELNET_SERVER_URL")
        self.server_url = resolved_server.rstrip("/") if resolved_server else None
        self.api_key = api_key or _load_default_api_key()
        self.push_to_server = push_to_server or bool(resolved_server)
        self.write_local_csv = write_local_csv

    def process_packet(self, packet_data):

        flow = self.tracker.add_packet(packet_data)

        session = self.session_tracker.add_flow(flow)

        features = extract_features(session)

        labeled_features = self.label_manager.add_labels(features)

        return labeled_features

    def _push_to_server(self, features: dict) -> bool:
        """
        POST session features to central server's /api/ingest endpoint.
        Returns True if successful, False otherwise.
        """
        if not self.server_url:
            return False

        target_url = self.server_url
        if not target_url.endswith("/api/ingest"):
            target_url = f"{target_url}/api/ingest"

        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            resp = requests.post(
                target_url,
                json=features,
                headers=headers,
                timeout=5.0
            )
            if resp.status_code in (200, 201):
                print(f"[+] Pushed session {features.get('session_id')} to {target_url} (HTTP {resp.status_code})")
                return True
            else:
                print(f"[!] Central server returned HTTP {resp.status_code} for session {features.get('session_id')}: {resp.text}")
                return False
        except Exception as exc:
            print(f"[!] Network error pushing to {target_url}: {exc}. Falling back to local CSV.")
            return False

    def save_features(self, features):
        """
        Persist features to central server and/or local CSV.
        If network push is enabled but fails, gracefully falls back to local CSV.
        """
        pushed = False
        if self.push_to_server and self.server_url:
            pushed = self._push_to_server(features)

        # Write locally if requested or if network push failed as fallback
        if self.write_local_csv or not pushed:
            save_to_csv(
                features,
                self.csv_file
            )

    def save_all_sessions(self):

        for session in self.session_tracker.sessions.values():

            features = extract_features(session)

            labeled_features = self.label_manager.add_labels(features)

            self.save_features(labeled_features)