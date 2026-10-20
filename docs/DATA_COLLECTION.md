# SentinelNet Lab Data Collection Runbook

This runbook guides the team through collecting real, multi-PC network session traffic for SentinelNet. The resulting CSV captures are merged and used to train and evaluate the machine learning classifier and anomaly detector.

---

## 1. Prerequisites & Environment Setup

Run the following checks on every lab PC before starting collection:
1. **Operating System:** Windows 10/11 (or Linux with root privileges).
2. **Python Environment:** Python 3.10+ with project dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. **Packet Sniffer Driver (Windows):** Install **Npcap** with *WinPcap API-compatible mode* and *Loopback Support* enabled.
4. **Permissions:** Open PowerShell or Command Prompt as **Administrator** on Windows (`sudo` on Linux).
5. **API Key Setup:** Set the environment variable or pass `--api-key`:
   ```powershell
   $env:SENTINELNET_API_KEY = "sentinelnet-lab-production-key-2026"
   ```

---

## 2. Collection Architecture & Targets

To train a robust model and avoid class imbalance:
- **Human Sessions:** Target at least **200 completed sessions**.
- **Tier 1 (Naive Bot):** Target at least **150 completed sessions**.
- **Tier 2 (Jittered Bot):** Target at least **150 completed sessions**.
- **Tier 3 (Mimicking Bot):** Target at least **150 completed sessions**.
- **Total Dataset Size:** At least **650 - 1,000 real sessions**.

---

## 3. Step-by-Step Collection Commands

### A. Collecting Real Human Traffic
Use dedicated PCs where team members engage in normal, authentic web browsing (e.g. visiting web servers, documentation portals, API endpoints on the test port):

On **PC 1 (Human Browsing Station)**:
```powershell
# Run PowerShell as Administrator:
python CN/agent/run_agent.py `
  --device-id "PC-HUMAN-01" `
  --label "Human" `
  --port 5000 `
  --server-url "http://<SERVER_IP>:5000" `
  --output-csv "data/real/pc_human_01.csv"
```
*Activity:* Browse the target web service normally. Click links, pause to read pages (3-15 seconds), perform multiple requests, and close tabs.
*Duration:* 20-30 minutes until ~100-200 sessions are accumulated. Press `Ctrl+C` to flush and save.

---

### B. Collecting Tier 1 Bot Traffic (Naive Bot)
On **PC 2 (Bot Station 1)**:
1. Start the agent sniffer with `--label Bot --bot-tier Tier1`:
   ```powershell
   python CN/agent/run_agent.py `
     --device-id "PC-BOT-TIER1" `
     --label "Bot" `
     --bot-tier "Tier1" `
     --port 5000 `
     --server-url "http://<SERVER_IP>:5000" `
     --output-csv "data/real/pc_bot_tier1.csv"
   ```
2. In a second terminal on the same PC, launch the Tier 1 bot traffic generator:
   ```powershell
   python bots/tier1_naive.py --target "http://<SERVER_IP>:5000/api/status" --requests 300 --interval 0.5
   ```
3. Stop the agent with `Ctrl+C` once the bot completes.

---

### C. Collecting Tier 2 Bot Traffic (Jittered Bot)
On **PC 3 (Bot Station 2)**:
1. Start the agent sniffer with `--label Bot --bot-tier Tier2`:
   ```powershell
   python CN/agent/run_agent.py `
     --device-id "PC-BOT-TIER2" `
     --label "Bot" `
     --bot-tier "Tier2" `
     --port 5000 `
     --server-url "http://<SERVER_IP>:5000" `
     --output-csv "data/real/pc_bot_tier2.csv"
   ```
2. In a second terminal, launch the Tier 2 bot:
   ```powershell
   python bots/tier2_jittered.py --target "http://<SERVER_IP>:5000" --requests 300 --min-interval 0.2 --max-interval 2.0
   ```
3. Stop the agent with `Ctrl+C` once complete.

---

### D. Collecting Tier 3 Bot Traffic (Mimicking Bot)
On **PC 4 (Bot Station 3)**:
1. Start the agent sniffer with `--label Bot --bot-tier Tier3`:
   ```powershell
   python CN/agent/run_agent.py `
     --device-id "PC-BOT-TIER3" `
     --label "Bot" `
     --bot-tier "Tier3" `
     --port 5000 `
     --server-url "http://<SERVER_IP>:5000" `
     --output-csv "data/real/pc_bot_tier3.csv"
   ```
2. In a second terminal, launch the Tier 3 bot:
   ```powershell
   python bots/tier3_mimicking.py --target "http://<SERVER_IP>:5000" --sessions 50
   ```
3. Stop the agent with `Ctrl+C` once complete.

---

## 4. How to Avoid Label Contamination

> [!CAUTION]
> Label contamination permanently ruins classifier ground truth. Follow these strict isolation rules:

1. **Dedicated Terminal / PC Isolation:** Never run human browsing on a machine running a bot script under the same sniffer session.
2. **Explicit Output Files:** Always pass distinct `--output-csv data/real/<device_role>.csv` arguments to ensure separate physical files.
3. **Single Ground-Truth Label:** Do not change `--label` in the middle of a capture session without restarting the agent.
4. **Port Isolation:** Ensure test traffic only flows over the monitored port (default 5000). Background OS traffic (Windows Update, telemetry) on other ports should be filtered out using `--port 5000`.

---

## 5. Aggregating and Building the Training Dataset

Once all lab CSVs are gathered into `data/real/`:
```
sentinelnet/
  data/
    real/
      pc_human_01.csv
      pc_human_02.csv
      pc_bot_tier1.csv
      pc_bot_tier2.csv
      pc_bot_tier3.csv
```

Run the validation and dataset builder:
```powershell
python ai/build_dataset.py --input-dir data/real --output data/processed/real_dataset.csv
```

Then train the models:
```powershell
python ai/train_models.py --data data/processed/real_dataset.csv
```
The model metadata will automatically be stamped with `"dataset_type": "real"` and reflected across the dashboard.
