# Visual Automation

Deterministic browser-automation system with a local computer-vision (OCR) component.
Runs a single Python process that launches Chromium, lets a user authenticate manually,
detects a target visual verification step, captures the image, runs PP-OCR locally on CPU,
validates the result, fills the input, submits, and verifies the outcome.

**Scope:** Authorized test environments, internal applications, QA systems, and websites you
own or have explicit permission to automate. This project does not implement or assist with
bypassing reCAPTCHA/hCaptcha/Turnstile, fingerprint evasion, proxy rotation, or any access
control evasion.

## Quick start

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium

# run against an authorized test site
./run.sh --config config/site.yaml
```

`run.sh` handles the Chromium library setup automatically (see below).
Exit code `0` on success, non-zero with diagnostics on failure.

## Run the bundled local test harness

The repository ships an authorized local test page + config so the whole flow can be
verified without any external site:

```bash
.venv/bin/python -m tools.serve_test_site        # terminal 1: serves the local page
.venv/bin/python -m app.main --config config/local-test.yaml
```

Or point `config/site.yaml` at any application you own / have permission to automate.

## Architecture

```
Browser Control -> Visual Capture + Processing -> OCR + Validation -> Workflow Decision + Action
```

- `app/browser/` Playwright session, locators, screenshots, actions, result verification
- `app/vision/`   OpenCV preprocessing variants
- `app/ocr/`      long-lived PP-OCR engine + regex/confidence validator
- `app/workflow/` explicit state machine, bounded retries, orchestrator
- `app/telemetry/` structured logs, run IDs, failure artifacts
- `config/`       all site behavior is configuration, not code

Design decisions (see the architecture doc): DOM-based element screenshots preferred over
full-page; PP-OCR loaded once per process; every OCR result validated before submission;
every retry bounded; success never assumed after a click; CPU-first, optimize only after
measuring.

## Security

`runtime/browser-profile/` may contain live authenticated cookies — treat it as a credential.
It is git-ignored, never bundle it with debug artifacts, and use a documented logout/reset
process when done.

## Tests

```bash
.venv/bin/python -m pytest
```

- unit: config parsing, validation, retry counters, state transitions, preprocessing
- integration: full open -> capture -> OCR -> fill -> submit -> verify against the local page

Run fast tests only (skips model-download and browser integration tests):

```bash
.venv/bin/python -m pytest -m "not slow"
```

### Chromium OS dependencies

On systems where `playwright install-deps` requires root (e.g. shared/WSL boxes), the
headless shell may fail with `libnss3.so not found`. Two options:

**No-root fallback (automatic):** `run.sh` and the test site config work out of the box —
`tools/ensure_chromium_deps.py` downloads and extracts the NSS/NSPR libraries into
`.chromium-deps/` (git-ignored) and sets `LD_LIBRARY_PATH` automatically.

```bash
./run.sh --config config/local-test.yaml
```

Or run it explicitly:

```bash
.venv/bin/python -m tools.ensure_chromium_deps
export LD_LIBRARY_PATH="<printed path>"
.venv/bin/python -m app.main --config config/local-test.yaml
```

**With root:** `sudo .venv/bin/python -m playwright install-deps chromium` fixes it
system-wide and no LD_LIBRARY_PATH workaround is needed.