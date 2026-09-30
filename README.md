# 🛡️ ThreatLens

**ThreatLens** is a Python-based cybersecurity desktop application focused on **URL analysis, validation, and future web security scanning workflows**.

The project is being developed as a **modular security analysis platform** with a Flet-based desktop interface and a Python-based CLI workflow for handling single and multiple URLs.

> 🚧 **Early Development — Active Prototype**

The current version focuses on building a clean application structure, URL input workflows, GUI navigation, and validation logic. A dedicated security scanning engine will be integrated in future development stages.

---

## ✨ Current Features

* 🔗 **Single URL Input**
* 🔗 **Multiple URL Input**
* 📁 **Import URLs from Text Files**
* 🖥️ **Flet-based Desktop GUI**
* 📊 **Dashboard & Sidebar Navigation**
* 🔍 **Basic URL Validation**
* 🧩 **Modular Project Architecture**
* ⚙️ **CLI + GUI Workflows**
* 🚧 **Scanner Engine Placeholder**

---

## 🎯 Project Goal

The long-term goal of ThreatLens is to provide a modular security analysis tool capable of examining URLs and web applications for potential security risks.

Planned analysis areas include:

* URL and domain analysis
* HTTP/HTTPS security checks
* Security header analysis
* Redirect analysis
* Technology detection
* Endpoint discovery
* Threat and risk categorization
* Security findings
* Scan result reporting

---

## 🖥️ Interface

ThreatLens uses **Flet** to provide a desktop application interface with a modern dashboard-style layout.

Current interface includes:

```text
┌──────────────────────────────────────────────┐
│                  ThreatLens                  │
├───────────────┬──────────────────────────────┤
│   Dashboard   │                              │
│   Scanner     │        Scanner Area          │
│   Settings    │                              │
│               │                              │
└───────────────┴──────────────────────────────┘
```

The GUI will continue to evolve as new scanning capabilities are added.

---

## 🧰 Technology Stack

| Technology              | Purpose                |
| ----------------------- | ---------------------- |
| 🐍 Python 3.10+         | Core application logic |
| 🖥️ Flet                | Desktop GUI            |
| 📄 Python File Handling | URL import & storage   |
| 🔗 HTTP/HTTPS           | Future web analysis    |
| 🧩 Modular Python       | Project architecture   |

---

## 📂 Project Structure

```text
ThreatLens/
│
├── main.py
├── README.md
├── requirements.txt
│
├── gui/
│   ├── __init__.py
│   ├── app.py
│   ├── background.py
│   ├── navigation.py
│   ├── sidebar.py
│   │
│   └── pages/
│       ├── m_input.py
│       ├── scan_url.py
│       └── single_input.py
│
├── modules/
│   ├── __init__.py
│   ├── url_chaker.py
│   └── url_impoter.py
│
└── .venv/
```

---

## ⚙️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/yashr3537/ThreatLens.git
cd ThreatLens
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

**Windows PowerShell:**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running ThreatLens

### 🖥️ GUI Application

```bash
python gui/app.py
```

### 💻 CLI Workflow

```bash
python main.py
```

---

## 🔗 URL Input Workflow

The current CLI supports:

```text
1. Single URL
2. Multiple URLs
3. Import URLs from a file
```

Example:

```text
Single URL:
https://example.com

Multiple URLs:
https://example.com, https://example.org
```

The GUI provides a dedicated scanner interface for handling URL-based workflows.

---

## 🛣️ Development Roadmap

ThreatLens is being developed incrementally.

### Phase 1 — Foundation ✅

* [x] Project structure
* [x] Python CLI workflow
* [x] Single URL input
* [x] Multiple URL input
* [x] File-based URL import
* [x] Basic URL validation
* [x] Flet desktop interface
* [x] Dashboard and navigation

### Phase 2 — Scanning Engine 🚧

* [ ] HTTP response checking
* [ ] Status code analysis
* [ ] Response-time measurement
* [ ] Redirect detection
* [ ] Security header analysis
* [ ] HTTPS/TLS checks

### Phase 3 — Security Analysis 🔍

* [ ] Domain analysis
* [ ] Technology detection
* [ ] Endpoint discovery
* [ ] CORS analysis
* [ ] Cookie security analysis
* [ ] Security findings
* [ ] Risk categorization

### Phase 4 — Reporting 📊

* [ ] Scan history
* [ ] JSON reports
* [ ] TXT reports
* [ ] Exportable results
* [ ] Detailed security summaries

---

## 🔐 Development Philosophy

ThreatLens is being built **step-by-step**, with each major feature developed and tested independently.

The focus is on:

**Modular code → Clean UI → Reliable scanning → Useful security findings**

Rather than implementing everything at once, the project will gradually evolve into a complete desktop security analysis platform.

---

## 🚧 Current Status

**ThreatLens is an early-stage cybersecurity project under active development.**

The current release primarily focuses on:

> **URL input + validation + desktop interface + project architecture**

The deeper security scanning engine is planned for upcoming development stages.

---

## 📌 Disclaimer

ThreatLens is intended for **authorized security testing, learning, and defensive security analysis**.

Only analyze systems and URLs that you own or have explicit permission to test.

---

## 👨‍💻 Development

Built with **Python + Flet** as an evolving cybersecurity project.

**ThreatLens — Analyze. Understand. Secure.**
