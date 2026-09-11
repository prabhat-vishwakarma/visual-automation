# Download & Install Guide

How to get this project onto your machine and run it.

---

## 1. What you need

| Requirement | Version |
|---|---|
| Python | 3.11 or newer |
| Operating system | Linux / macOS / Windows (WSL recommended on Windows) |
| Internet | Required for first install & model download |
| Disk space | ~3 GB for dependencies + OCR models |

---

## 2. Get the files

The project is a private repository. Get access one of these ways:

**If you received a GitHub invite:**
```bash
git clone https://github.com/prabhat-vishwakarma/visual-automation.git
cd visual-automation
```

**If you received a ZIP file:** extract it, then open a terminal and go into the
extracted `visual-automation/` folder:
```bash
cd <path-to-extracted>/visual-automation
```

---

## 3. Install

**Step 1 — create a virtual environment and install dependencies:**
```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt
```

> On Windows with native Python use `.venv\Scripts\pip` instead of `.venv/bin/pip`.
> If your system Python is older than 3.11, install Python 3.11+ first.

**Step 2 — install the Chromium browser Playwright needs:**
```bash
.venv/bin/python -m playwright install chromium
```

**Optional — system libraries for Chromium (Linux):**
The bundled `run.sh` handles this automatically on Linux without root. If you
have root and prefer system-wide packages:
```bash
sudo .venv/bin/python -m playwright install-deps chromium
```

---

## 4. Try it out (built-in demo)

The repo ships an authorized local test page so you can verify everything works:

**Terminal 1 — start the local test page:**
```bash
.venv/bin/python -m tools.serve_test_site --port 8800
```

**Terminal 2 — run the automation:**
```bash
./run.sh --config config/local-test.yaml
```

You should see structured log output ending in:
```
"event": "run_finished", "success": true, "state": "COMPLETE"
```

Exit code `0` means success. The browser reads the code in the challenge image,
fills the input, clicks Continue, and verifies the result — all automatically.

---

## 5. Use it on your own site

1. Copy `config/site.yaml` to a new file (or edit it).
2. Set:
   - `target.start_url` — the page to automate
   - `selectors.*` — the CSS selectors for the image, input, button, success/reject markers
   - `ocr.expected_regex` — the expected format of the code (default `^[A-Z0-9]{5}$`)
   - `browser.headless` — `false` to watch it run in a visible browser
3. Run:
   ```bash
   ./run.sh --config config/site.yaml
   ```
   If `authentication.mode` is `manual`, log in to the app by hand when the browser
   window opens; the workflow waits and then takes over.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| `libnss3.so not found` (Linux Chromium) | `run.sh` fixes this automatically. Or run `sudo .venv/bin/python -m playwright install-deps chromium` |
| `All variants rejected ... low_confidence` | Lower `ocr.min_confidence` in the config or improve the image (larger crop, clearer text) |
| `TargetNotFound` | The selectors in `selectors.*` don't match the page — fix them for your site |
| Python version error | Install Python 3.11+ and recreate the `.venv` |

---

## 7. Scope reminder

This tool is for **authorized test environments, internal applications, QA systems,
and websites you own or have explicit permission to automate**. It is not designed
for, and does not assist with, bypassing reCAPTCHA, hCaptcha, Cloudflare, or any
other anti-abuse system.