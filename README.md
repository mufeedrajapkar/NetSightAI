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
- **Overview**: Real-time summary cards, prediction distribution donut chart, and recent flow telemetry.
- **Live Traffic**: Replay Tier 1, 2, and 3 PCAP files with instant feature extraction and classification.
- **AI Analysis**: In-depth inspection of the 9 model contract features and class probability estimates.
- **Bot Analysis**: 3-tier comparative matrix and domain shift explanation.
- **Architecture**: End-to-end pipeline topology and domain breakdown (Computer Networks vs AI).
- **About Project**: Project one-liner, objectives, and actual technology stack.

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

