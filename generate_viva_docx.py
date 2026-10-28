"""
generate_viva_docx.py
---------------------
Generates the comprehensive, professional SentinelNet Viva Master Guide (.docx).
Covers everything start to end for academic evaluation, viva preparation, and demonstrations.
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    """Set background color of a table cell."""
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tc_pr.append(shd)

def create_viva_document(output_path: str):
    doc = docx.Document()

    # Page Margins: 1 inch on all sides
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)

    # Styles & Colors
    # Primary: Deep Navy (#1E293B), Accent: Cobalt Blue (#2563EB), Dark Gray (#334155)
    COLOR_PRIMARY = RGBColor(30, 41, 59)
    COLOR_ACCENT = RGBColor(37, 99, 235)
    COLOR_DARK = RGBColor(51, 65, 85)
    COLOR_MUTED = RGBColor(100, 116, 139)

    # Document Title Block
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("SENTINELNET")
    title_run.font.size = Pt(28)
    title_run.font.bold = True
    title_run.font.color.rgb = COLOR_ACCENT

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("Real-Time Network Flow Behavioral Intelligence & Multi-Tier Bot Classification\nComprehensive Project & Viva Preparation Master Guide")
    sub_run.font.size = Pt(14)
    sub_run.font.bold = True
    sub_run.font.color.rgb = COLOR_PRIMARY

    meta_p = doc.add_paragraph()
    meta_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta_run = meta_p.add_run("Computer Networks & Artificial Intelligence Integrated Project | Semester 5\nEvaluation Ready Reference Document\n")
    meta_run.font.size = Pt(10)
    meta_run.font.italic = True
    meta_run.font.color.rgb = COLOR_MUTED

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    def add_h1(text):
        h = doc.add_heading(text, level=1)
        h.paragraph_format.space_before = Pt(18)
        h.paragraph_format.space_after = Pt(6)
        for r in h.runs:
            r.font.size = Pt(16)
            r.font.bold = True
            r.font.color.rgb = COLOR_ACCENT
        return h

    def add_h2(text):
        h = doc.add_heading(text, level=2)
        h.paragraph_format.space_before = Pt(12)
        h.paragraph_format.space_after = Pt(4)
        for r in h.runs:
            r.font.size = Pt(13)
            r.font.bold = True
            r.font.color.rgb = COLOR_PRIMARY
        return h

    def add_p(text, bold_prefix="", space_after=6):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.line_spacing = 1.15
        if bold_prefix:
            b_run = p.add_run(bold_prefix)
            b_run.bold = True
            b_run.font.color.rgb = COLOR_PRIMARY
        r = p.add_run(text)
        r.font.size = Pt(10.5)
        r.font.color.rgb = COLOR_DARK
        return p

    def add_callout(text, title="KEY VIVA TAKEAWAY"):
        table = doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_background(cell, "F1F5F9")  # soft slate
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.1)
        p.paragraph_format.right_indent = Inches(0.1)
        
        t_run = p.add_run(f"[{title}] ")
        t_run.bold = True
        t_run.font.size = Pt(10)
        t_run.font.color.rgb = COLOR_ACCENT
        
        c_run = p.add_run(text)
        c_run.font.size = Pt(10)
        c_run.font.color.rgb = COLOR_DARK
        doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # -------------------------------------------------------------
    # CHAPTER 1: EXECUTIVE SUMMARY & PROBLEM STATEMENT
    # -------------------------------------------------------------
    add_h1("1. Executive Summary & Problem Statement")
    add_p(
        "SentinelNet is a dual-domain engineering system combining Computer Networks (CN) packet/flow analysis with "
        "Artificial Intelligence (AI) supervised classification and unsupervised anomaly detection. It solves the critical "
        "failure of traditional firewalls: their inability to identify sophisticated automated bots that evade detection by mimicking human pacing."
    )
    add_p(
        "Standard Web Application Firewalls (WAFs) and Intrusion Detection Systems (IDS) rely heavily on static IP blocklists, "
        "rate thresholds (e.g., maximum 10 requests/second), and fixed User-Agent header rules. Modern automated threats—such as "
        "credential stuffers, web scrapers, and Layer 7 denial-of-service botnets—deliberately introduce randomized jitter delays "
        "(0.2s - 2.0s) and sample inter-arrival delays from empirical human browsing data to slip completely undetected through linear rate limiters.",
        bold_prefix="The Core Vulnerability: "
    )
    add_callout(
        "SentinelNet demonstrates that traditional rate limits and linear ML models (like Logistic Regression) fail completely "
        "against jittered (Tier 2) and mimicking (Tier 3) bots. SentinelNet resolves this by combining 9 statistical transport/flow features, "
        "a Non-Linear Random Forest Ensemble, and an Isolation Forest Anomaly Detector with a 3-class verdict: Human, Bot, and Suspicious.",
        title="CORE PROJECT THESIS"
    )

    # -------------------------------------------------------------
    # CHAPTER 2: END-TO-END SYSTEM ARCHITECTURE
    # -------------------------------------------------------------
    add_h1("2. End-to-End System Architecture (The 4-Stage Pipeline)")
    add_p("The SentinelNet pipeline is strictly decoupled into 4 modular engineering stages:")

    # Table of Pipeline Stages
    stage_table = doc.add_table(rows=5, cols=4)
    stage_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    headers = ["Stage", "Name", "Primary Responsibility", "Key Technologies"]
    for i, h in enumerate(headers):
        cell = stage_table.cell(0, i)
        set_cell_background(cell, "1E293B")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    stages_data = [
        ("1", "Traffic Ingestion", "Captures raw packets, manages PCAP replay, or aggregates live L7 HTTP streams in real-time.", "Scapy, Npcap, Zero-Admin HTTP Aggregator"),
        ("2", "Feature Extraction", "Extracts bidirectional session metrics without inspecting encrypted payload bytes.", "SessionTracker, FlowTracker, Contract v1.0"),
        ("3", "AI Inference Engine", "Computes supervised class probability & unsupervised isolation anomaly score.", "RandomForest, LogisticRegression, IsolationForest"),
        ("4", "Security Dashboard", "Renders live packet telemetry, bot tier difficulty curves, and flow modals.", "React 18, TypeScript, TailwindCSS, Vite")
    ]

    for row_idx, data in enumerate(stages_data, 1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, text in enumerate(data):
            cell = stage_table.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(9)
            r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------
    # CHAPTER 3: THE 9 CONTRACT FLOW FEATURES (CN DOMAIN)
    # -------------------------------------------------------------
    add_h1("3. The 9 Network Flow Features (Data Contract v1.0)")
    add_p(
        "SentinelNet adheres to a strict 9-feature data contract. Crucially, the system does NOT inspect packet payload contents. "
        "This ensures end-to-end privacy preservation, compatibility with TLS 1.3 encrypted HTTPS traffic, and high line-rate throughput."
    )

    feat_table = doc.add_table(rows=10, cols=4)
    feat_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    feat_headers = ["Feature Name", "Type", "Unit / Formula", "Networking & AI Significance"]
    for i, h in enumerate(feat_headers):
        cell = feat_table.cell(0, i)
        set_cell_background(cell, "2563EB")
        p = cell.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = RGBColor(255, 255, 255)

    features_data = [
        ("requests_per_sec", "Continuous", "reqs / duration", "Captures session intensity; high values catch Tier 1 naive flooders."),
        ("session_duration", "Continuous", "t_last - t_first (sec)", "Total active connection lifespan for the flow."),
        ("packet_size_mean", "Continuous", "mean(bytes)", "Distinguishes lightweight API queries from rich web asset payloads."),
        ("packet_size_var", "Continuous", "var(bytes)", "Humans fetch diverse assets (images, CSS, HTML); bots fetch uniform responses."),
        ("request_interval_mean", "Continuous", "mean(delta_t) (sec)", "Average inter-arrival delay between successive packets/requests."),
        ("request_interval_var", "Continuous", "var(delta_t) (sec^2)", "Measures timing irregularity; mechanical bots have near-zero variance."),
        ("bytes_transferred", "Integer", "sum(bytes)", "Total cumulative data payload volume exchanged in session."),
        ("num_connections", "Integer", "count(distinct conns)", "Measures transport socket fanout and concurrency."),
        ("protocol", "Categorical", "TCP / UDP", "Transport protocol identifier; One-Hot Encoded during ML preprocessing.")
    ]

    for row_idx, data in enumerate(features_data, 1):
        bg = "FFFFFF" if row_idx % 2 != 0 else "F8FAFC"
        for col_idx, text in enumerate(data):
            cell = feat_table.cell(row_idx, col_idx)
            set_cell_background(cell, bg)
            p = cell.paragraphs[0]
            r = p.add_run(text)
            r.font.size = Pt(8.5)
            r.font.color.rgb = COLOR_DARK

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # -------------------------------------------------------------
    # CHAPTER 4: THE 4 BOT SOPHISTICATION TIERS
    # -------------------------------------------------------------
    add_h1("4. The 4 Bot Sophistication Tiers & Evasion Profiles")
    add_p(
        "A standout research contribution of SentinelNet is the implementation of 4 distinct bot sophistication tiers "
        "designed to test the boundaries of machine learning detection:"
    )

    add_h2("Tier 1: Naive Script Bot (Deterministic)")
    add_p("Mechanically issues rapid HTTP GET requests at a fixed 0.15s – 0.5s interval to a single endpoint. It exhibits zero timing variance and abnormal packet rates (~7 pkts/sec). Both linear and non-linear classifiers catch it with 100% precision.")

    add_h2("Tier 2: Jittered Bot (Uniform Random Delay)")
    add_p("Introduces uniform random delays U(0.2s, 1.5s) to simulate pauses. Average delay is ~0.85s, which directly mimics the Human baseline average (0.807s).")
    add_callout(
        "Tier 2 successfully evaded the baseline Logistic Regression model because a linear hyperplane only evaluates packet rate. "
        "However, SentinelNet catches Tier 2 using the Variance-to-Mean Ratio (VMR): VMR = variance / mean. "
        "For uniform jitter U(a, b), VMR is unnaturally low (< 0.28). Real humans have reading bursts and pauses resulting in high VMR (> 0.50).",
        title="WHY TIER 2 EVADES & HOW WE CATCH IT"
    )

    add_h2("Tier 3: Human-Mimicking Bot (Empirical Delay Resampling)")
    add_p("Draws delay intervals directly from real-world human click recordings (human_intervals.csv) and inserts 5-15s simulated 'reading pauses'. It navigates realistic multi-step browsing graphs (Home -> Search -> Product -> Login) and periodically rotates User-Agent strings. It evades basic rate filters but is flagged by Isolation Forest anomaly scores and multi-UA client fingerprinting.")

    add_h2("Tier 4: Adversarial Evasion Bot (Bounded Perturbation)")
    add_p("Employs deliberate mathematical perturbation noise to minimize the classifier's confidence score while keeping total duration bounded, exposing model boundary vulnerabilities.")

    # -------------------------------------------------------------
    # CHAPTER 5: ARTIFICIAL INTELLIGENCE & HYBRID ARBITRATION
    # -------------------------------------------------------------
    add_h1("5. Artificial Intelligence: Models, Training & Hybrid Verdict")
    add_p(
        "The machine learning pipeline implements a leak-free Scikit-Learn Pipeline combining ColumnTransformer "
        "(StandardScaler for numerical metrics, OneHotEncoder for protocol), Stratified 5-Fold Cross Validation, and GridSearchCV."
    )

    add_h2("Comparative Model Evaluation")
    add_p(
        "The system evaluates multiple algorithms: Logistic Regression (linear baseline), Support Vector Classifier (RBF kernel), "
        "Gradient Boosting (GBDT), and Random Forest. Random Forest was selected as the champion model for its ability to learn non-linear "
        "multi-feature rules without overfitting."
    )

    add_h2("The 3-Class Output & Hybrid Anomaly Arbiter")
    add_p("Rather than a binary Human vs Bot decision, SentinelNet outputs three classes: Human, Bot, and Suspicious.")
    add_p("1. Supervised Verdict: Random Forest estimates probability distribution [P(Human), P(Bot), P(Suspicious)].", bold_prefix="Dual Arbitration Rules: ")
    add_p("2. Anomaly Guardrail: Isolation Forest (trained exclusively on verified Human traffic) calculates an anomaly score. If the classifier predicts 'Human' but the Isolation Forest flags an anomaly (score < -0.05) OR top confidence is under 0.60, SentinelNet escalates the final verdict to 'Suspicious'.")
    add_p("3. Telemetry Guardrail: If client packets exhibit python-requests fingerprints or rotate User-Agent headers mid-session, the traffic is flagged immediately.")

    # -------------------------------------------------------------
    # CHAPTER 6: LIVE MULTI-DEVICE COLLEGE NETWORK DEMONSTRATION
    # -------------------------------------------------------------
    add_h1("6. Live Multi-Device College Network Deployment")
    add_p(
        "SentinelNet was demonstrated live in a college computer lab across multiple physical devices on a shared network:"
    )
    add_p("• Main Server (Laptop): Runs Flask API backend on 0.0.0.0:5001 and Vite React dashboard on port 5173.")
    add_p("• Normal User (Lab PC): Standard browsing without administrator rights or packet capture drivers.")
    add_p("• Attacker Machines (Friends' Laptops): Firing Tier 1, Tier 2, and Tier 3 bot scripts over the network.")
    add_callout(
        "College campus Wi-Fi networks enforce Access Point (AP) Client Isolation, which blocks peer-to-peer traffic between devices. "
        "We solved this by connecting all machines to a shared local mobile hotspot (172.16.227.x subnet) and building a "
        "Zero-Admin L7 HTTP Stream Aggregator into the backend server so client PCs required zero driver installations.",
        title="PRACTICAL NETWORKING CHALLENGE SOLVED"
    )

    # -------------------------------------------------------------
    # CHAPTER 7: TOP 30 VIVA QUESTIONS & MODEL ANSWERS
    # -------------------------------------------------------------
    add_h1("7. Top 30 High-Frequency Viva Questions & Expert Answers")

    qa_list = [
        ("Q1: What is SentinelNet in one concise sentence?",
         "SentinelNet is a real-time network security intelligence system that classifies network flows into Human, Bot, or Suspicious by combining 9 transport/flow behavioral features with a Random Forest ensemble and an Isolation Forest anomaly detector."),

        ("Q2: Why do you analyze network flows instead of inspecting packet payloads?",
         "Payload inspection (Deep Packet Inspection) fails when traffic is encrypted (HTTPS/TLS 1.3), violates user privacy, and incurs severe CPU overhead. Flow-based behavioral analysis works seamlessly on encrypted traffic at full line rate."),

        ("Q3: What are the 9 features in your data contract?",
         "requests_per_sec, session_duration, packet_size_mean, packet_size_var, request_interval_mean, request_interval_var, bytes_transferred, num_connections, and protocol."),

        ("Q4: Why was Tier 2 bot initially classified as Human by Logistic Regression?",
         "Tier 2 bot uses uniform random delays (0.2s - 1.5s), giving an average delay of ~0.85s. This matches the human dataset average delay (0.807s). Logistic Regression is a linear classifier that relies heavily on rate and duration; because the rate fell inside the human cluster, it was fooled."),

        ("Q5: How did you fix the Tier 2 evasion?",
         "We upgraded to a non-linear Random Forest ensemble and implemented the Variance-to-Mean Ratio (VMR). Uniform random delays have an unnaturally low VMR (< 0.28) and lack human reading pauses (> 2.5s), allowing us to reliably flag them."),

        ("Q6: What is Variance-to-Mean Ratio (VMR) and why is it important?",
         "VMR = variance / mean. Human browsing is bursty: quick clicks followed by 5–20s reading pauses, giving high VMR (> 0.50). Uniform random bot delays have flat distributions with low variance, producing low VMR (< 0.28)."),

        ("Q7: What is Tier 3 bot and how does it operate?",
         "Tier 3 is a human-mimicking bot that samples delay intervals directly from real human recordings (human_intervals.csv), inserts reading pauses, navigates multi-step URL paths, and rotates User-Agents."),

        ("Q8: How do you catch Tier 3 bots if their timing mimics humans?",
         "We catch Tier 3 using L7 telemetry inspection: detecting rotating User-Agent headers from the same IP (which humans never do), detecting headless/script headers, and using the Isolation Forest anomaly detector."),

        ("Q9: Why does SentinelNet have 3 classes (Human, Bot, Suspicious) instead of 2?",
         "Binary classification forces uncertain or novel evasion attacks into either Human or Bot. 'Suspicious' serves as a crucial gray-zone buffer for anomaly detection disagreements or low model confidence (< 0.60), alerting security analysts to inspect the session."),

        ("Q10: What is an Isolation Forest and how is it used in SentinelNet?",
         "Isolation Forest is an unsupervised anomaly detection algorithm that isolates anomalies by randomly partitioning feature spaces. We train it exclusively on known Human baseline traffic so any abnormal flow geometry is flagged as an anomaly."),

        ("Q11: Why did you choose Macro F1-score as your primary evaluation metric?",
         "In security datasets, classes are often imbalanced. Accuracy is misleading because a model predicting only the majority class can get high accuracy. Macro F1 calculates the unweighted mean of F1 across Human, Bot, and Suspicious, treating all classes with equal importance."),

        ("Q12: How did you prevent data leakage during machine learning training?",
         "We used a Scikit-Learn Pipeline where StandardScaler and OneHotEncoder are fitted ONLY on the training folds during cross-validation, and never on the held-out test set."),

        ("Q13: What cross-validation technique was used?",
         "Stratified 5-Fold Cross-Validation, ensuring that each fold preserves the exact percentage distribution of Human, Bot, and Suspicious classes."),

        ("Q14: What is the difference between TCP and UDP in your system?",
         "TCP is connection-oriented and stateful with flow control (used for HTTP/browsing); UDP is connectionless and datagram-based (used for DNS/streaming). The protocol feature is one-hot encoded."),

        ("Q15: How does your system handle encrypted HTTPS traffic?",
         "Since we only measure packet inter-arrival times, packet sizes, duration, and connection counts (all extracted from IP/TCP headers without touching payload), HTTPS encryption does not impact our feature extraction."),

        ("Q16: How did you run the live demonstration in your college lab?",
         "Our laptop ran the Flask backend on 0.0.0.0:5001 and React frontend. A lab PC generated human browsing traffic. Two friends' laptops ran Tier 1, 2, and 3 bot scripts over a shared mobile hotspot to bypass campus AP isolation."),

        ("Q17: Why was a mobile hotspot needed instead of college Wi-Fi?",
         "Enterprise college Wi-Fi implements Access Point (AP) Client Isolation, which forbids device-to-device socket connections. The mobile hotspot provided direct LAN routing across the 172.16.227.x subnet."),

        ("Q18: What is the Zero-Admin L7 Session Aggregator?",
         "Windows lab PCs lack administrator rights and Npcap packet capture drivers. To overcome this, we built an L7 session aggregator directly into backend_server.py that groups incoming HTTP requests by client IP and extracts flow features dynamically at the server."),

        ("Q19: What is the role of the AI Bridge (ai_bridge.py)?",
         "AI Bridge acts as the decoupled interface between the Computer Networks flow engine and the AI models. It validates contract features, caches the trained pipeline, computes inference, and applies hybrid arbitration."),

        ("Q20: What happens if an attacker slows down requests to 1 request per hour?",
         "This is a low-and-slow attack. While it avoids rate triggers, its session duration and inter-arrival mean become extreme outliers, triggering the Isolation Forest anomaly detector."),

        ("Q21: What is the difference between Logistic Regression and Random Forest?",
         "Logistic Regression is a linear classifier that finds a single flat decision boundary. Random Forest is an ensemble of 200 decision trees that constructs complex, non-linear boundaries capable of capturing multi-feature interactions."),

        ("Q22: What are the hyperparameters of your Random Forest model?",
         "n_estimators=200 (number of trees), max_depth=None, min_samples_split=5, min_samples_leaf=1, class_weight='balanced'."),

        ("Q23: How do you calculate packet size variance, and why does it matter?",
         "Variance of packet byte sizes. Automated bots hitting an API endpoint receive uniform JSON responses (low variance). Real humans browsing receive varied responses: images, HTML, fonts, and scripts (high variance)."),

        ("Q24: What is the Bot Tier Difficulty Curve on the dashboard?",
         "It is an empirical visualization showing how model detection F1-score degrades as bot sophistication advances from Tier 1 (1.00 F1) to Tier 2 (jittered), Tier 3 (mimicking), and Tier 4 (adversarial)."),

        ("Q25: What is PCAP replay mode?",
         "An offline testing mode that reads saved packet capture (.pcap) files from disk, replays them through the flow processor, and evaluates model predictions without requiring a live network connection."),

        ("Q26: What frontend technologies did you use?",
         "React 18 with TypeScript, Vite build tool, TailwindCSS for responsive styling, Lucide-React icons, and custom glassmorphism components with live polling."),

        ("Q27: How does SentinelNet secure its API endpoints?",
         "The backend enforces API key authentication via the SENTINELNET_API_KEY environment variable and X-API-Key request headers."),

        ("Q28: What is SHAP and how is it used in your AI module?",
         "SHAP (SHapley Additive exPlanations) is a game-theoretic approach to explain model decisions, showing which features contributed most to flagging a flow as Bot or Human."),

        ("Q29: How many automated tests exist in your codebase?",
         "102 automated unit and integration tests covering feature extraction, flow aggregation, AI Bridge inference, anomaly detection, PCAP replay, and backend REST endpoints. All 102 tests pass."),

        ("Q30: What is the main conclusion of the project?",
         "Static firewall rules and linear ML are fundamentally inadequate against modern bots. Behavioral transport flow metrics combined with non-linear tree ensembles and anomaly detection provide robust, privacy-preserving defense even against sophisticated human-mimicking bots.")
    ]

    for q, a in qa_list:
        add_p(a, bold_prefix=f"{q}\n", space_after=8)

    # -------------------------------------------------------------
    # CHAPTER 8: QUICK REVISION FORMULA & CHEAT SHEET
    # -------------------------------------------------------------
    add_h1("8. Quick Revision Cheat Sheet & Formula Card")
    
    cheat_table = doc.add_table(rows=6, cols=2)
    cheat_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    cheat_table.cell(0, 0).paragraphs[0].add_run("Metric / Concept").bold = True
    cheat_table.cell(0, 1).paragraphs[0].add_run("Formula & Meaning").bold = True
    set_cell_background(cheat_table.cell(0, 0), "1E293B")
    set_cell_background(cheat_table.cell(0, 1), "1E293B")
    cheat_table.cell(0, 0).paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)
    cheat_table.cell(0, 1).paragraphs[0].runs[0].font.color.rgb = RGBColor(255, 255, 255)

    cheat_data = [
        ("Variance-to-Mean Ratio (VMR)", "VMR = sigma^2 / mu. Low (< 0.28) = Uniform Jitter Bot. High (> 0.50) = Real Human Bursts."),
        ("Macro F1-Score", "Macro F1 = (F1_human + F1_bot + F1_suspicious) / 3. Equal weight to all classes."),
        ("F1-Score Formula", "F1 = 2 * (Precision * Recall) / (Precision + Recall). Harmonic mean."),
        ("Linear Classifier Failure", "Tier 2 delay mean = (0.2 + 1.5)/2 = 0.85s. Human mean = 0.807s. Linear hyperplane fails."),
        ("Hybrid Verdict Rule", "IF (Raw == 'Human' AND Anomaly == True) OR (Prob < 0.60) -> Verdict = 'Suspicious'.")
    ]

    for r_idx, (col1, col2) in enumerate(cheat_data, 1):
        bg = "FFFFFF" if r_idx % 2 != 0 else "F8FAFC"
        c1, c2 = cheat_table.cell(r_idx, 0), cheat_table.cell(r_idx, 1)
        set_cell_background(c1, bg)
        set_cell_background(c2, bg)
        p1, p2 = c1.paragraphs[0], c2.paragraphs[0]
        r1, r2 = p1.add_run(col1), p2.add_run(col2)
        r1.bold = True
        r1.font.size = Pt(9)
        r2.font.size = Pt(9)

    doc.add_paragraph().paragraph_format.space_after = Pt(12)
    doc.save(output_path)
    print(f"[+] Successfully generated master viva guide at: {output_path}")

if __name__ == "__main__":
    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SentinelNet_Viva_Master_Guide.docx")
    create_viva_document(out_file)
