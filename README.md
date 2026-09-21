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
python -m pytest CN/tests -v
```

### 🚀 One-Line Summary

```text
Capture → Parse → Flow → Session → Features → Label → CSV → Merge → Validate → AI/ML
```

> **Note:** Run packet capture with the required Windows/Npcap permissions. For multi-PC dataset collection, run the capture agent separately on each participating PC and use the appropriate `--device-id`, `--label`, and `--bot-tier`.
