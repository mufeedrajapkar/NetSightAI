# SentinelNet

**SentinelNet** is a Network Security research project for classifying HTTP traffic into Human, Naive Bot, Jittered Bot, and Human-Mimicking Bot behaviors for Computer Networks (CN), AI academic coursework.

## Project Modules

- **[`bots/`](file:///c:/College/SEM-5/CN-AI-Project/sentinelnet/bots/README.md)**: Synthetic bot traffic generator suite (`tier1_naive.py`, `tier2_jittered.py`, `tier3_mimicking.py`), interactive human traffic recorder (`human_recorder.py`), and test server (`test_server.py`).

Refer to [`bots/README.md`](file:///c:/College/SEM-5/CN-AI-Project/sentinelnet/bots/README.md) for full instructions on running the traffic generator tiers and test server.

# ⚡ CN Quick Start

Run the following commands from the **SentinelNet project root**.

### 1. Create and activate virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install scapy pytest pandas
```

> **Windows:** Make sure **Npcap** is installed and running before starting packet capture.

### 3. Run a Human traffic capture

```powershell
python -m CN.agent.capture.test_capture --device-id PC01 --duration 60 --label Human --bot-tier None --output CN/data/raw/PC01.csv
```

Generate normal browsing traffic while the capture is running.

### 4. Run Bot captures

**Tier 1 — Naive Bot**

```powershell
python -m CN.agent.capture.test_capture --device-id PC02 --duration 60 --label Bot --bot-tier Tier1 --output CN/data/raw/PC02.csv
```

**Tier 2 — Jittered Bot**

```powershell
python -m CN.agent.capture.test_capture --device-id PC03 --duration 60 --label Bot --bot-tier Tier2 --output CN/data/raw/PC03.csv
```

**Tier 3 — Human-Mimicking Bot**

```powershell
python -m CN.agent.capture.test_capture --device-id PC04 --duration 60 --label Bot --bot-tier Tier3 --output CN/data/raw/PC04.csv
```

### 5. Merge all PC datasets

```powershell
python -m CN.agent.merge_csv
```

Output:

```text
CN/data/processed/sentinelnet_dataset.csv
```

### 6. Validate the dataset

```powershell
python -c "import pandas as pd; df=pd.read_csv('CN/data/processed/sentinelnet_dataset.csv'); print('Rows:',len(df)); print('Columns:',list(df.columns)); print('Missing:',df.isnull().sum().sum()); print('Duplicates:',df.duplicated().sum())"
```

### 7. Run CN tests

```powershell
.venv\Scripts\python -m pytest CN/tests -v
```

---

## 🌐 SentinelNet Web Intelligence Dashboard

A minimalist, dark-themed network intelligence dashboard connecting the frontend directly to the existing Computer Networks and AI classification pipeline.

### Starting the Dashboard:

#### 1. Configure the API Key:
Create a `.env` file in the project root (see `.env.example`):
```powershell
Copy-Item .env.example .env
```
Set `SENTINELNET_API_KEY=your-secure-random-key` in `.env` (or via `$env:SENTINELNET_API_KEY`). **The server will refuse to start without a configured API key.**

#### 2. Start the Backend API Server:
```powershell
python CN\web\backend_server.py
```
*(Runs on `http://127.0.0.1:5000`)*

#### 3. Start the Frontend Dashboard:
```powershell
cd frontend
npm run dev
```
*(Open `http://127.0.0.1:5173` in your browser)*

### Dashboard Capabilities:
- **Overview**: Real-time summary cards, multi-device security threat matrix, prediction distribution donut chart, and recent flow telemetry with dataset provenance indicator (`real` vs `synthetic prototype`).
- **Live Traffic**: Live multi-device session stream, start/stop live packet sniffing, and manual Tier 1, 2, and 3 PCAP replay.
- **AI Analysis**: In-depth inspection of the 9 model contract features, Isolation Forest anomaly score, and class probability estimates.
- **Bot Analysis**: 3-tier comparative matrix with real empirical F1 difficulty curve plot, least-separated features (Cohen's d), and Tier 4 Adversarial Evasion Robustness Benchmark.
- **Architecture**: End-to-end pipeline topology and domain breakdown (Computer Networks vs AI).
- **About Project**: Project one-liner, objectives, and actual technology stack.

---

## 📡 Live Multi-Device Network Pipeline (Distributed Lab Setup)

SentinelNet supports real-time multi-PC ingestion. Each PC in the lab runs its own local capture agent and pushes completed sessions to the central server.

### 1. Configure Shared Secret & Central Server URL
On both the central server and remote PCs, set the shared API key and server URL using either environment variables or a gitignored `.env` file (see `.env.example`):

**Via `.env` (recommended):**
```bash
# Copy template
copy .env.example .env

# Edit .env with your shared secret
SENTINELNET_API_KEY=your_shared_lab_secret_key
SENTINELNET_SERVER_URL=http://<CENTRAL_SERVER_IP>:5000
```

**Via PowerShell:**
```powershell
$env:SENTINELNET_API_KEY = "your_shared_lab_secret_key"
$env:SENTINELNET_SERVER_URL = "http://192.168.1.100:5000"
```

### 2. Run Capture Agents on Lab PCs
On each lab PC (e.g., PC01, PC02, PC03), run the capture agent with streaming enabled:

```powershell
python -m CN.agent.capture.test_capture --device-id PC02 --duration 60 --label Bot --bot-tier Tier1 --push --server-url http://192.168.1.100:5000
```

Or run the dedicated standalone capture CLI:
```powershell
python CN\agent\run_agent.py --device-id PC01 --duration 60 --label Human --push
```

### 3. Graceful Fallback
If the central server goes down or is unreachable, the agent automatically logs the error and saves all sessions to the local CSV without crashing.

---

## 🚀 One-Command End-to-End System Demonstration

Run the automated full-system demonstration:

```powershell
python run_demo.py
```

This starts an embedded server, ingests Human, Bot, and Anomalous traffic via `/api/ingest`, queries the Isolation Forest anomaly detector, runs the hybrid Suspicious consensus engine, and prints the Bot Tier and Adversarial evaluation benchmarks.

### 🧪 Model Training & Dataset Pipeline

- **Data Collection Runbook**: `docs/DATA_COLLECTION.md`
- **Aggregate Captures**: `python ai/build_dataset.py --input-dir CN/data/raw --output data/processed/sentinelnet_real_dataset.csv`
- **Train Classifier**: `python ai/train_models.py --data data/processed/sentinelnet_real_dataset.csv`
- **Train Anomaly Detector**: `python ai/anomaly_detection.py`
- **Bot Tier Difficulty Analysis**: `python ai/bot_tier_analysis.py`
- **Adversarial Robustness Evaluation**: `python ai/adversarial_eval.py`

### 🚀 Pipeline Summary

```text
Traffic Source → Packet Capture / PCAP Replay → Packet Parser → Flow Tracking → Feature Extraction → AI Bridge (Classifier + Isolation Forest) → Hybrid Verdict Engine → Dashboard
```

