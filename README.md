# gdoc2site

`gdoc2site` is a Python tool that exports every **tab** in a Google Doc as a standalone HTML page, producing a complete static website. Each tab becomes a separate HTML file wrapped in a Jinja2 template, with Google redirect URLs cleaned and content simplified for deployment.

This repository contains the main script: **`gdoc2site.py`**.

---

## ✨ Features

- Exports **each tab** from a Google Doc as its own HTML file  
- Supports exporting:
  - **All tabs**
  - **A single tab** (via command-line argument)
- Cleans wrapped Google redirect links (e.g., `https://www.google.com/url?q=...`)
- Extracts only the `<body>` content from Google’s HTML export
- Applies a Jinja2-based HTML template (`base.html`) to each exported page
- Outputs to an `articles/` directory
- Handles OAuth authentication automatically (stores `token.json`)

---

## 📦 Setup

- Create Google Cloud Project and Enable Google Docs and Drive APIs
- Create OAuth Credentials
  - APIs & Services -> Credentials
  - OAuth Client ID -> Desktop Application
  - Download JSON credential file and save it in credentials.json

The first run will launch a browser window for authentication and create
token.json.

- Install dependencies via:

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

- Export all tabs
```bash
python gdoc2site.py
```

- Export specific tab (exports only the tab with the matching ID)
```bash
python gdoc2site.py <TAB_ID>
```
