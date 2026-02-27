# Cybersecurity Intelligence Newsletter Automation System

A production-grade Python application that automates the collection, synthesis, and delivery of a weekly cybersecurity intelligence briefing.

## Features

- **Automated Scraping**: Pulls RSS, XML, JS-rendered HTML, and Telegram channels. Filters strictly to current week's news.
- **AI Synthesis**: Uses Gemini API (free tier) to synthesize unstructured intel into a cohesive format with a strict anti-hallucination validation post-check.
- **Business-class PDF**: Generates a high-quality, Apple-aesthetic PDF using `WeasyPrint` and HTML/CSS templates.
- **WhatsApp Formatter**: Automatically limits characters and formats the output for easy distribution via WhatsApp groups.
- **Gmail SMTP Integration**: Automates emailing the HTML summary and PDF attachment directly to stakeholders.
- **Robust Scheduling**: Uses `APScheduler` to run unconditionally every Monday.

## Setup Instructions

### Environment Setup

1. Copy `.env.example` to `.env`:

   ```bash
   cp .env.example .env
   ```

2. Open `.env` and fill in necessary keys:
   - **GEMINI_API_KEY**: Get a free key from Google AI Studio.
   - **GMAIL Credentials**: If `SEND_EMAIL=true`, provide an App Password (not your account password) generated from Google Account -> Security.

### Installation

Run the provided setup script on your Debian/Ubuntu or OSX machine. It installs pip requirements and required system libraries.

```bash
bash setup.sh
```

**Manual installation**:

```bash
pip install -r requirements.txt
playwright install chromium
```

*(You may additionally need system-level fonts and libpango for WeasyPrint depending on your OS. See WeasyPrint docs).*

## Usage

### Run Manually

Generate the newsletter immediately:

```bash
python cyber_newsletter.py --run-now
```

Running tests to verify pipeline components quickly:

```bash
python test_run.py
```

### Run as Scheduler Daemon

Run the script continuously to process automatically every Monday at 08:00 AM (configured Timezone in `.env`):

```bash
python cyber_newsletter.py
```

*(In production, you'd likely wrap this in a docker container, `systemd` service, or `tmux`/`screen` session).*

## Troubleshooting

- `playwright failure`: Ensure `playwright install chromium` was run.
- `pdf failure (Pango/Cairo)`: `weasyprint` has strict system dependencies. On Windows, you might need GTK3. On Linux, `libpango-1.0-0` is required. If it fails, the system safely falls back to outputting a `.txt` file instead.
- `Gmail SMTP Error 535`: Ensure 2-Factor Authentication is ON for the Gmail account, and use the 16-character string from "App Passwords".
