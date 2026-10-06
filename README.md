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

#### 1. Start the Backend API Server:
```powershell
.venv\Scripts\python CN\web\backend_server.py
```
*(Runs on `http://127.0.0.1:5001`)*

#### 2. Start the Frontend Dashboard:
```powershell
cd frontend
npm run dev
```
*(Open `http://127.0.0.1:5173` in your browser)*

### Dashboard Capabilities:
- **Overview**: Real-time summary cards, multi-device security threat matrix, prediction distribution donut chart, and recent flow telemetry.
- **Live Traffic**: Live multi-device session stream and manual Tier 1, 2, and 3 PCAP replay.
- **AI Analysis**: In-depth inspection of the 9 model contract features and class probability estimates.
- **Bot Analysis**: 3-tier comparative matrix and domain shift explanation.
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
SENTINELNET_SERVER_URL=http://<CENTRAL_SERVER_IP>:5001
```

**Via PowerShell:**
```powershell
$env:SENTINELNET_API_KEY = "your_shared_lab_secret_key"
$env:SENTINELNET_SERVER_URL = "http://192.168.1.100:5001"
```

### 2. Run Capture Agents on Lab PCs
On each lab PC (e.g., PC01, PC02, PC03), run the capture agent with streaming enabled:

```powershell
python -m CN.agent.capture.test_capture --device-id PC02 --duration 60 --label Bot --bot-tier Tier1 --push --server-url http://192.168.1.100:5001
```

**Key Flags:**
- `--push`: Enables live pushing of completed sessions to `/api/ingest`.
- `--server-url <URL>`: Points to the central backend server (defaults to `SENTINELNET_SERVER_URL` env var).
- `--api-key <KEY>`: Overrides API key (defaults to `SENTINELNET_API_KEY` env var or `.env`).
- `--no-local-csv`: Skips local CSV writes on successful network push (still saves to local CSV automatically if server is unreachable).

### 3. Graceful Fallback
If the central server goes down or is unreachable, the agent automatically logs the error and saves all sessions to the local CSV without crashing.

---


## 🖥️ CLI Final Academic Demonstration

Run the automated offline PCAP replay across all three bot tiers:

```powershell
.venv\Scripts\python CN\demos\run_final_demo.py
```

### 🚀 Pipeline Summary

```text
Traffic Source → Packet Capture / PCAP Replay → Packet Parser → Flow Tracking → Feature Extraction → AI Bridge → ML Classifier → Dashboard
```

