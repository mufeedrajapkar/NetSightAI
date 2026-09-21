# SentinelNet - Synthetic Bot Traffic Generator Suite

A Python suite for generating synthetic HTTP traffic tier classifications (Naive Bot, Jittered Bot, Human-Mimicking Bot, and Human Baseline) to train downstream Machine Learning classifiers for Network Security research (CN/AI projects).

---

## Suite Directory Overview

```text
bots/
├── test_server.py        # Light Flask server providing test endpoints
├── tier1_naive.py        # Tier 1: Fixed-interval naive bot generator
├── tier2_jittered.py     # Tier 2: Uniformly jittered random bot generator
├── tier3_mimicking.py    # Tier 3: Human-mimicking bot with empirical interval sampling
├── human_recorder.py     # Interactive tool to record real human inter-arrival timing
├── logger_utils.py       # Standardized CSV/JSON traffic logging helper
├── human_intervals.csv   # Pre-populated empirical human timing dataset
├── requirements.txt      # Python package dependencies
└── README.md             # Usage documentation & CLI reference
```

---

## 1. Setup & Installation

1. Navigate to the `bots/` directory:
   ```bash
   cd bots
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 2. Launch the Target Test Server

Start the local Flask test server before running any generator scripts. It binds to `http://127.0.0.1:5000` by default.

```bash
python test_server.py --host 127.0.0.1 --port 5000
```

Available server endpoints:
- `GET /` (Home HTML page)
- `GET /api/data` (Mock telemetry JSON API)
- `GET /search?q=<query>` (Search endpoint)
- `GET /product/<id>` (Product details endpoint)
- `POST /login` (Mock authentication endpoint)

---

## 3. Running the Bot Traffic Generators

### Tier 1 — Naive Bot (`tier1_naive.py`)
Sends HTTP GET requests at a **fixed interval** using a **single hardcoded User-Agent**. Deterministic and trivially detectable.

```bash
python tier1_naive.py --target-url http://127.0.0.1:5000/ --duration 30 --interval 0.5 --label bot_tier1 --output-log tier1_log.csv
```

**Parameters:**
- `--target-url`: Target server URL (default: `http://127.0.0.1:5000/`).
- `--duration`: Total runtime in seconds (default: `30`).
- `--interval`: Fixed delay in seconds between requests (default: `0.5`).
- `--label`: Ground-truth tag (default: `bot_tier1`).
- `--output-log`: Output log path (`.csv` or `.json`, default: `tier1_log.csv`).

---

### Tier 2 — Jittered Bot (`tier2_jittered.py`)
Sends requests with **uniform random inter-arrival delays**, randomizes search query parameters, and **rotates User-Agent headers**. Moderately detectable.

```bash
python tier2_jittered.py --target-url http://127.0.0.1:5000 --duration 45 --min-interval 0.2 --max-interval 2.0 --label bot_tier2 --output-log tier2_log.csv
```

**Parameters:**
- `--min-interval`: Minimum random delay in seconds (default: `0.2`).
- `--max-interval`: Maximum random delay in seconds (default: `2.0`).

---

### Tier 3 — Human-Mimicking Bot (`tier3_mimicking.py`)
Resamples inter-arrival times directly from an **empirical human dataset** (`human_intervals.csv`), periodically inserts **human reading/thinking pauses** (5-15s), and executes **realistic stateful navigation session flows**. Hardest to distinguish from human traffic.

```bash
python tier3_mimicking.py --target-url http://127.0.0.1:5000 --duration 60 --intervals-file human_intervals.csv --pause-chance 0.05 --label bot_tier3 --output-log tier3_log.csv
```

**Parameters:**
- `--intervals-file`: Path to CSV file containing recorded human inter-arrival float values (default: `human_intervals.csv`).
- `--pause-chance`: Probability per request of introducing a reading pause (default: `0.05` / 5%).
- `--pause-min`: Minimum think time pause in seconds (default: `5.0`).
- `--pause-max`: Maximum think time pause in seconds (default: `15.0`).

---

## 4. Recording Genuine Human Traffic (`human_recorder.py`)

To collect empirical human timing data for Tier 3, run `human_recorder.py`. You manually trigger requests by pressing `[ENTER]`. The script calculates inter-arrival delays and appends them to `human_intervals.csv`.

```bash
python human_recorder.py --target-url http://127.0.0.1:5000 --output-intervals human_intervals.csv --output-log human_log.csv --label human
```

---

## 5. Dataset Log Schema

All traffic generators write to standard CSV/JSON logs with ground-truth labels for ML feature extraction:

| Column | Description | Example |
| :--- | :--- | :--- |
| `timestamp` | UTC ISO-8601 timestamp | `2026-09-14T08:35:00.123456+00:00` |
| `url` | Full target request URL | `http://127.0.0.1:5000/search?q=security` |
| `response_time_ms` | HTTP round-trip latency in milliseconds | `12.4` |
| `status_code` | HTTP status code | `200` |
| `label` | Ground-truth class label | `bot_tier1`, `bot_tier2`, `bot_tier3`, `human` |

---

## Safety & Academic Guidelines
This traffic generator suite is designed exclusively for academic research against local or authorized lab servers. Keep request rates within safe limits (default 1-5 req/sec).
