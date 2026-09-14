# SentinelNet — Computer Networks Module

## Overview

The Computer Networks (CN) module of SentinelNet is responsible for collecting and transforming network traffic into structured session-level data for AI/ML-based traffic classification.

The CN pipeline is:

**Network Traffic → Packet Capture → Packet Parsing → 5-Tuple Flow Identification → Flow Tracking → Sessionization → Feature Extraction → Labeling → CSV Dataset**

Each participating PC runs a lightweight SentinelNet capture agent. This is required because a switched LAN does not allow one PC to passively observe all unicast traffic from other PCs.

The system collects **network metadata and statistical features**, not application payloads or HTTPS content.

---

## CN Responsibilities

The CN module performs the following tasks:

1. Capture network packets using Scapy.
2. Parse packets into structured metadata.
3. Identify network flows using a normalized bidirectional 5-tuple.
4. Track packets belonging to the same flow.
5. Convert flows into sessions using an inactivity timeout.
6. Extract statistical traffic features.
7. Assign Human/Bot labels and bot tiers.
8. Store session-level data in CSV format.
9. Merge data collected from multiple PCs into one dataset.
10. Validate the final dataset before passing it to the AI/ML module.

---

## CN Architecture

```text
                    Network Traffic
                           |
                           v
                  +------------------+
                  | Packet Capture   |
                  |     Scapy        |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Packet Parser    |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Flow Key         |
                  | 5-Tuple          |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Flow Tracker     |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Session Tracker  |
                  | Timeout = 5 sec  |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Feature          |
                  | Extraction       |
                  +------------------+
                           |
                           v
                  +------------------+
                  | Label Manager    |
                  +------------------+
                           |
                           v
                  +------------------+
                  | CSV Writer       |
                  +------------------+
                           |
                           v
                  sentinelnet_dataset.csv
                           |
                           v
                         AI/ML
```

---

# Technologies Used

* **Python 3**
* **Scapy** — packet capture and packet parsing
* **Npcap** — Windows packet capture support
* **CSV** — dataset storage
* **Git/GitHub** — version control

---

# Project Structure

```text
CN/
│
├── agent/
│   ├── capture/
│   │   ├── packet_parser.py
│   │   └── test_capture.py
│   │
│   ├── flow/
│   │   ├── flow_key.py
│   │   ├── flow_tracker.py
│   │   ├── flow_processor.py
│   │   └── __init__.py
│   │
│   ├── session/
│   │   ├── session_tracker.py
│   │   └── __init__.py
│   │
│   ├── features.py
│   ├── label_manager.py
│   ├── csv_writer.py
│   └── merge_csv.py
│
├── data/
│   ├── raw/
│   │   ├── PC01.csv
│   │   ├── PC02.csv
│   │   ├── PC03.csv
│   │   └── PC04.csv
│   │
│   └── processed/
│       └── sentinelnet_dataset.csv
│
├── tests/
│   ├── test_flow_key.py
│   ├── test_flow_tracker.py
│   ├── test_flow_processor.py
│   ├── test_session_tracker.py
│   ├── test_features.py
│   ├── test_label_manager.py
│   └── test_csv_writer.py
│
└── __init__.py
```

---

# Installation

## 1. Clone the Repository

```powershell
git clone <repository-url>
cd "CN - SEM V"
```

If the repository is already cloned:

```powershell
cd "CN - SEM V"
```

---

## 2. Create a Virtual Environment

Windows PowerShell:

```powershell
python -m venv venv
```

Activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

Expected prompt:

```text
(venv) PS C:\Users\<username>\Desktop\CN - SEM V>
```

---

## 3. Install Scapy

```powershell
pip install scapy
```

Verify:

```powershell
python -c "import scapy; print('Scapy installed successfully')"
```

---

## 4. Install Npcap

On Windows, SentinelNet requires **Npcap** for packet capture.

After installing Npcap, verify that the service is running:

```powershell
sc.exe query npcap
```

If necessary:

```powershell
sc.exe start npcap
```

Run packet capture from an **Administrator PowerShell** if required by the Windows/Npcap configuration.

---

# Running the CN Capture Agent

The capture agent is located at:

```text
CN/agent/capture/test_capture.py
```

From the project root:

```powershell
python -m CN.agent.capture.test_capture
```

Default configuration:

```text
Device  : PC01
Label   : Human
Bot Tier: None
Duration: 30 seconds
```

The agent captures packets for 30 seconds and automatically saves the collected sessions.

---

# Capture Agent Options

The agent supports the following command-line arguments:

| Argument      | Description                 | Default                   |
| ------------- | --------------------------- | ------------------------- |
| `--device-id` | Device identifier           | `PC01`                    |
| `--duration`  | Capture duration in seconds | `30`                      |
| `--label`     | Traffic label               | `Human`                   |
| `--bot-tier`  | Bot difficulty tier         | `None`                    |
| `--output`    | CSV output file             | `sentinelnet_dataset.csv` |

---

# Human Traffic Collection

For a Human-labelled PC:

```powershell
python -m CN.agent.capture.test_capture --device-id PC01 --duration 60 --label Human --bot-tier None --output CN/data/raw/PC01.csv
```

While the capture is running, generate normal browsing traffic such as:

* Open websites
* Search Google
* Browse multiple pages
* Scroll through pages
* Watch short videos
* Open/close browser tabs

The agent will display information similar to:

```text
Session: PC01_S1 | Device: PC01 | Label: Human | Tier: None | Packets: 25 | Bytes: 18240
```

---

# Bot Traffic Collection

SentinelNet uses three bot traffic tiers.

## Tier 1 — Naive Fixed-Interval Bot

Tier 1 represents a simple bot with predictable timing.

Run the capture agent:

```powershell
python -m CN.agent.capture.test_capture --device-id PC02 --duration 60 --label Bot --bot-tier Tier1 --output CN/data/raw/PC02.csv
```

---

## Tier 2 — Jittered Bot

Tier 2 introduces randomized timing between requests to make the traffic less predictable.

```powershell
python -m CN.agent.capture.test_capture --device-id PC03 --duration 60 --label Bot --bot-tier Tier2 --output CN/data/raw/PC03.csv
```

---

## Tier 3 — Human-Mimicking Bot

Tier 3 generates delays based on human traffic timing distributions.

```powershell
python -m CN.agent.capture.test_capture --device-id PC04 --duration 60 --label Bot --bot-tier Tier3 --output CN/data/raw/PC04.csv
```

The purpose of the three tiers is to create progressively harder classification cases:

```text
Tier 1
  |
  v
Predictable / obvious bot
  |
  v
Tier 2
  |
  v
Randomized / jittered bot
  |
  v
Tier 3
  |
  v
Human-like bot
```

---

# Flow Identification

SentinelNet identifies a flow using:

```text
Source IP
Source Port
Destination IP
Destination Port
Protocol
```

This forms a network 5-tuple.

The flow key is normalized so that packets travelling in both directions belong to the same bidirectional flow.

Example:

```text
192.168.1.10:5000 → 142.250.183.14:443 TCP
```

and

```text
142.250.183.14:443 → 192.168.1.10:5000 TCP
```

are treated as the same flow.

---

# Sessionization

Flows are converted into sessions using an inactivity timeout.

Current configuration:

```text
Session timeout = 5 seconds
```

If a flow becomes inactive beyond the configured timeout, it is treated as no longer active.

Each session receives a unique identifier such as:

```text
PC01_S1
PC01_S2
PC02_S1
```

---

# Extracted Features

The CN module extracts the following session-level features:

| Feature                | Description                  |
| ---------------------- | ---------------------------- |
| `session_id`           | Unique session identifier    |
| `device_id`            | PC/device identifier         |
| `session_duration`     | Duration of the session      |
| `packets_per_sec`      | Packet transmission rate     |
| `packet_size_mean`     | Average packet size          |
| `packet_size_var`      | Variance of packet sizes     |
| `packet_interval_mean` | Average time between packets |
| `packet_interval_var`  | Variance of packet intervals |
| `bytes_transferred`    | Total bytes transferred      |
| `packet_count`         | Number of packets            |
| `protocol`             | Network protocol             |
| `label`                | Human or Bot                 |
| `bot_tier`             | None, Tier1, Tier2, or Tier3 |

---

# Dataset Format

The final dataset contains:

```text
session_id,
device_id,
session_duration,
packets_per_sec,
packet_size_mean,
packet_size_var,
packet_interval_mean,
packet_interval_var,
bytes_transferred,
packet_count,
protocol,
label,
bot_tier
```

Example:

```csv
session_id,device_id,session_duration,packets_per_sec,packet_size_mean,packet_size_var,packet_interval_mean,packet_interval_var,bytes_transferred,packet_count,protocol,label,bot_tier
PC01_S1,PC01,12.4,4.03,512.2,14321.4,0.248,0.019,63500,50,TCP,Human,None
PC02_S1,PC02,10.8,8.15,421.6,9821.2,0.123,0.011,45500,88,TCP,Bot,Tier1
```

---

# Merging PC Datasets

After collecting traffic from all PCs, merge the individual datasets:

```powershell
python -m CN.agent.merge_csv
```

The script reads:

```text
CN/data/raw/PC01.csv
CN/data/raw/PC02.csv
CN/data/raw/PC03.csv
CN/data/raw/PC04.csv
```

and generates:

```text
CN/data/processed/sentinelnet_dataset.csv
```

---

# Dataset Validation

Check the generated CSV:

```powershell
python -c "import pandas as pd; df=pd.read_csv('CN/data/processed/sentinelnet_dataset.csv'); print(df.head()); print('\nShape:', df.shape); print('\nMissing values:\n', df.isnull().sum()); print('\nDuplicates:', df.duplicated().sum())"
```

Expected validation conditions:

```text
Required columns present
Missing values = 0
Duplicate rows = 0
Human and Bot samples present
Tier1, Tier2 and Tier3 bot samples present
```

---

# Running Unit Tests

Run all CN tests:

```powershell
python -m pytest CN/tests -v
```

If `pytest` is not installed:

```powershell
pip install pytest
```

Then:

```powershell
python -m pytest CN/tests -v
```

Individual tests can also be executed:

```powershell
python -m pytest CN/tests/test_flow_key.py -v
```

```powershell
python -m pytest CN/tests/test_flow_tracker.py -v
```

```powershell
python -m pytest CN/tests/test_session_tracker.py -v
```

```powershell
python -m pytest CN/tests/test_features.py -v
```

```powershell
python -m pytest CN/tests/test_label_manager.py -v
```

```powershell
python -m pytest CN/tests/test_csv_writer.py -v
```

---

# Complete CN Workflow

From a fresh environment:

```powershell
# Activate environment
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install scapy pytest pandas

# Run Human capture
python -m CN.agent.capture.test_capture --device-id PC01 --duration 60 --label Human --bot-tier None --output CN/data/raw/PC01.csv

# Run Tier 1 capture
python -m CN.agent.capture.test_capture --device-id PC02 --duration 60 --label Bot --bot-tier Tier1 --output CN/data/raw/PC02.csv

# Run Tier 2 capture
python -m CN.agent.capture.test_capture --device-id PC03 --duration 60 --label Bot --bot-tier Tier2 --output CN/data/raw/PC03.csv

# Run Tier 3 capture
python -m CN.agent.capture.test_capture --device-id PC04 --duration 60 --label Bot --bot-tier Tier3 --output CN/data/raw/PC04.csv

# Merge datasets
python -m CN.agent.merge_csv

# Run tests
python -m pytest CN/tests -v

# Validate dataset
python -c "import pandas as pd; df=pd.read_csv('CN/data/processed/sentinelnet_dataset.csv'); print('Rows:',len(df)); print('Columns:',list(df.columns)); print('Missing:',df.isnull().sum().sum()); print('Duplicates:',df.duplicated().sum())"
```

---

# Dataset Collection Configuration

| Device | Traffic Type          | Label | Bot Tier |
| ------ | --------------------- | ----- | -------- |
| PC01   | Normal human browsing | Human | None     |
| PC02   | Naive bot             | Bot   | Tier1    |
| PC03   | Jittered bot          | Bot   | Tier2    |
| PC04   | Human-mimicking bot   | Bot   | Tier3    |

---

# Privacy and Network Design

SentinelNet follows a metadata-based network monitoring approach.

The CN module:

* Does not inspect HTTPS payload contents.
* Does not perform ARP spoofing.
* Does not perform Man-in-the-Middle interception.
* Does not collect application message contents.
* Extracts packet and session-level statistical metadata.
* Uses lightweight agents on participating PCs.

This makes the system suitable for controlled laboratory experimentation while maintaining a clear separation between network monitoring and application payload inspection.

---

# Output

The final CN output is:

```text
CN/data/processed/sentinelnet_dataset.csv
```

This dataset is passed to the **AI/ML module**, which uses the extracted network features to classify traffic as:

```text
Human
Bot
Suspicious
```

The CN module therefore acts as the **network data acquisition and feature-generation layer** of SentinelNet.
