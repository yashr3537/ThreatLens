# 🛡️ ThreatLens

**ThreatLens** is a Python/Flet desktop application with a modular C++17 Phase 1 reconnaissance scanner for authorized targets.

The Flet GUI launches the C++17 scanner as a child process and reads its JSON results. The scanner provides target profiling, DNS resolution, paced subdomain discovery, host inventory, and configurable TCP port/service checks.

> 🚧 **Early Development — Active Prototype**

The project is an active prototype. Build the Phase 1 scanner executable before starting a GUI scan.

---

## ✨ Current Features

* 🔗 **Single URL Input**
* 🔗 **Multiple URL Input**
* 📁 **Import URLs from Text Files**
* 🖥️ **Flet-based Desktop GUI**
* 📊 **Dashboard & Sidebar Navigation**
* 🔍 **Basic URL Validation**
* 🧭 **C++ Phase 1 target and DNS profiling**
* 🌐 **Paced, configurable subdomain and host discovery**
* 🔌 **Configurable IPv4/IPv6 TCP port and service inventory**
* 📄 **Latest report retained across navigation with clipboard, TXT, and PDF export**
* 🧩 **Modular Project Architecture**
* ⚙️ **CLI + GUI Workflows**

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
| ⚙️ C++17                | Phase 1 scanner        |
| 🪟 Windows Winsock      | DNS and TCP networking |
| 🔗 HTTP/HTTPS           | Future web analysis    |
| 🧩 Modular Python       | Project architecture   |

---

## 📂 Project Structure

```text
ThreatLens/
│
├── main.py
├── scanner.cpp                 # Older standalone JSON prototype
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
│       ├── scan_url.py            # Async C++ process and JSON handling
│       └── single_input.py
│
├── modules/
│   ├── __init__.py
│   ├── url_chaker.py
│   └── url_impoter.py
│
└── scanner/
    ├── main.cpp                # Phase 1 console entrypoint
    ├── analysis/               # Reserved for a later phase
    ├── core/
    │   ├── result.cpp / result.h
    │   ├── scanner.cpp / scanner.h
    │   └── target.cpp / target.h
    ├── discovery/
    │   └── subdomain.cpp / subdomain.h
    ├── network/
    │   ├── dns.cpp / dns.h
    │   ├── host.cpp / host.h
    │   └── port.cpp / port.h
    ├── output/
    │   ├── json.cpp / json.h
    │   └── report.cpp / report.h
    └── web/                    # Reserved for a later phase
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

### 🛡️ C++ Phase 1 Scanner (Windows)

The C++ scanner requires a Windows C++17 compiler with Winsock support. With MSYS2 UCRT64 GCC installed, the GUI builds `scanner_gui.exe` automatically on the first scan and rebuilds it when scanner sources change. To build it manually, run this from the repository root in PowerShell:

```powershell
C:\msys64\ucrt64\bin\g++.exe -std=c++17 -Wall -Wextra scanner/main.cpp scanner/core/target.cpp scanner/network/dns.cpp scanner/network/host.cpp scanner/network/port.cpp scanner/discovery/subdomain.cpp scanner/output/json.cpp -lws2_32 -pthread -o scanner_gui.exe
python gui/app.py
```

The GUI requires an HTTP/HTTPS URL and explicit authorization confirmation. For subdomains, enter a wordlist file path with one label per line, or leave it blank for the built-in list. DNS candidates are paced and capped by default.

Choose common TCP ports by default, enter a comma-separated port list, or explicitly confirm a full TCP port range. Connection timeout and concurrency are configurable and capped. Closed and timed-out ports are omitted from the open-port results. Banner data is best-effort and may be empty.

Only scan systems you own or are explicitly authorized to assess. Full-range scans can take longer and create more network traffic.

---

## 🔗 URL Input Workflow

The Python CLI supports:

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

The Flet single-target page launches `scanner_gui.exe` without a shell, passes the selected scan settings as arguments, and renders the JSON response in the five Phase 1 sections. The latest report stays available while navigating and can be copied or exported as TXT/PDF from Reports. Start the GUI with `python gui/app.py`; on the first scan it builds the executable if needed and displays compiler errors in the page.

---

## 🛣️ Development Roadmap

ThreatLens is being developed incrementally.

### Phase 1 — Foundation and C++ Recon ✅

* [x] Project structure
* [x] Python CLI workflow
* [x] Single URL input
* [x] Multiple URL input
* [x] File-based URL import
* [x] Basic URL validation
* [x] Flet desktop interface
* [x] Dashboard and navigation
* [x] Target profile and DNS resolution
* [x] Configurable, paced subdomain discovery
* [x] Structured IPv4/IPv6 host inventory
* [x] Configurable TCP port and service inventory
* [x] Connect the Phase 1 scanner to the Flet GUI

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

> **Python URL workflows + Flet interface + standalone C++ Phase 1 scanner**

The deeper security scanning engine is planned for upcoming development stages.

---

## 📌 Disclaimer

ThreatLens is intended for **authorized security testing, learning, and defensive security analysis**.

Only analyze systems and URLs that you own or have explicit permission to test.

---

## 👨‍💻 Development

Built with **Python + Flet** as an evolving cybersecurity project.

**ThreatLens — Analyze. Understand. Secure.**
