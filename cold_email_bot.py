#!/usr/bin/env python3
"""
Cold Email Automation Bot for Gopi M
Sends personalized internship inquiry emails to Canadian AI/ML/Tech startups.

SETUP:
  pip install secure-smtplib (built-in) — uses stdlib smtplib
  Gmail: Enable 2FA → Google Account → Security → App Passwords → Generate one
  
USAGE:
  python3 cold_email_bot.py --mode dry_run          # Preview first 5 emails
  python3 cold_email_bot.py --mode send --tier ai    # Send to AI/ML companies only
  python3 cold_email_bot.py --mode send --tier all   # Send to all 2307 companies
  python3 cold_email_bot.py --mode resume            # Resume from last sent (reads log)
"""

import csv
import re
import smtplib
import time
import json
import os
import sys
import argparse
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SENDER_NAME   = "Gopi M"
SENDER_EMAIL  = "gopim302004@gmail.com"      # ← your Gmail
GMAIL_APP_PWD = " cvko ghel usls wqqr"        # ← paste your App Password here

CSV_PATH      = "Canadian Businesses - Sheet1.csv"
LOG_PATH      = "sent_log.json"
DELAY_SECONDS = 8          # seconds between emails (avoid spam triggers)
BATCH_SIZE    = 50         # pause every N emails for a longer break
BATCH_PAUSE   = 120        # seconds to pause between batches

PORTFOLIO     = "https://gopi30.vercel.app"
GITHUB        = "https://github.com/Gopikrish-30"
HUGGINGFACE   = "https://huggingface.co/gopi30"
LINKEDIN      = "https://www.linkedin.com/in/gopi-m/"
PHONE         = "+91 6379190477"
TARGET_ROLE   = "AI Engineer Internship / ML Engineer Internship"
# ──────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)s  %(message)s",
    handlers=[
        logging.FileHandler("email_bot.log"),
        logging.StreamHandler(sys.stdout),
    ]
)
log = logging.getLogger(__name__)


# ─── COMPANY DATA EXTRACTION ──────────────────────────────────────────────────

AI_KEYWORDS = [
    'artificial intelligence', 'machine learning', 'deep learning', 'nlp',
    'computer vision', 'data science', 'llm', 'generative ai', 'neural',
    'natural language', 'transformer', 'language model', 'chatbot', 'ai-powered',
    'ai powered', 'predictive analytics', 'ai platform', 'ai tools',
]
TECH_KEYWORDS = [
    'software', 'saas', 'technology', 'platform', 'cloud', 'developer tools',
    'devops', 'cybersecurity', 'data analytics', 'information technology',
    'fintech', 'healthtech', 'edtech', 'digital', 'automation',
]


def extract_name(row: dict) -> str:
    """Pull real company name from short_description or permalink."""
    desc = row.get('short_description', '')
    m = re.match(
        r'^(.+?)\s+(?:is\s+(?:a|an|the)|provides|offers|develops|builds|creates|specializes)',
        desc, re.IGNORECASE
    )
    if m:
        name = m.group(1).strip()
        if len(name) < 60:
            return name
    permalink = row.get('permalink', '')
    if permalink:
        clean = re.sub(r'-[a-f0-9]{4}$', '', permalink)
        return clean.replace('-', ' ').title()
    return 'Your Company'


def is_valid_email(email: str) -> bool:
    pattern = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'
    return bool(email and re.match(pattern, email.strip()))


def resolve_csv_path(csv_path: str) -> str:
    path = Path(csv_path)
    if path.exists():
        return str(path)

    alternatives = [
        Path(__file__).with_name("Canadian Businesses - Sheet1.csv"),
        Path(__file__).with_name("Canadian_Businesses_-_Sheet1.csv"),
    ]
    for alternative in alternatives:
        if alternative.exists():
            return str(alternative)

    return csv_path


def load_companies(csv_path: str, tier: str = 'all') -> list[dict]:
    companies = {'ai': [], 'tech': [], 'all': []}
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            email = row.get('contact_email', '').strip()
            if not is_valid_email(email):
                continue
            if row.get('operating_status', '') != 'active':
                continue

            text = (
                row.get('description', '') + ' ' +
                row.get('short_description', '') + ' ' +
                row.get('categories', '') + ' ' +
                row.get('category_groups', '')
            ).lower()

            is_ai   = any(kw in text for kw in AI_KEYWORDS)
            is_tech = any(kw in text for kw in TECH_KEYWORDS)

            entry = {
                'company_name': extract_name(row),
                'email':        email,
                'website':      row.get('website', ''),
                'linkedin':     row.get('linkedin', ''),
                'location':     row.get('locations', '').split(';')[0].strip(),
                'description':  row.get('short_description', '')[:180],
                'categories':   row.get('categories', ''),
                'tier':         'ai' if is_ai else 'tech' if is_tech else 'general',
            }
            if tier == 'all':
                companies['all'].append(entry)
            elif tier == 'ai' and is_ai:
                companies['ai'].append(entry)
            elif tier == 'tech' and is_tech:
                companies['tech'].append(entry)

    if tier == 'ai':
        return companies['ai']
    elif tier == 'tech':
        return companies['tech']
    else:
        return companies['all']


# ─── EMAIL TEMPLATES ──────────────────────────────────────────────────────────

def subject(company: dict, campaign_tier: str) -> str:
    return "AI Engineering Internship Enquiry — Gopi M"


def body_html(company: dict, campaign_tier: str) -> str:
    name = company['company_name']

    intro = (
        "I'm Gopi — a 2× national-level hackathon winner and AI/ML engineer focused on building reliable "
        "systems around LLMs, RAG pipelines, and AI agents. I'm reaching out to ask whether you have any "
        f"remote {TARGET_ROLE} openings — internship, part-time, or otherwise."
    )
    experience = (
        "Over the past year I shipped several AI systems: a fine-tuned translation model with 100+ downloads "
        "on HuggingFace, an AI agent for desktop automation that won Best Technical Implementation at "
        "NEOVERSE'26, a safety-aligned LLM fine-tuned on legal data using Constitutional AI and RLAIF, and "
        "a RAG-based research pipeline built for hallucination resistance. I also completed an 8-month ML "
        "engineering internship building computer vision systems and deploying production applications with "
        "Django and React."
    )

    return f"""<!DOCTYPE html>
<html>
<head>
  <style>
    body {{
      font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;
      color: #111111;
      font-size: 15px;
      line-height: 1.85;
      max-width: 580px;
      margin: 0 auto;
      padding: 0;
    }}
    p {{ margin: 0 0 16px 0; }}
    a {{ color: #111111; }}
    .links {{
      font-size: 13px;
      color: #666;
      margin: 20px 0;
      line-height: 2.1;
    }}
    .links a {{
      color: #111;
      text-decoration: none;
      border-bottom: 1px solid #ccc;
    }}
    .sig {{
      border-top: 1px solid #eee;
      margin-top: 24px;
      padding-top: 16px;
      font-size: 13px;
      color: #555;
    }}
  </style>
</head>
<body>

  <p>Hi {name} team,</p>

    <p>{intro}</p>

    <p>{experience}</p>

  <p>My approach: I build complete systems — not just notebooks. Before reaching for an LLM I always
  ask whether a simpler approach solves the problem — that question alone keeps systems fast,
  maintainable, and cheap to run.</p>

    <div class="links">
        Portfolio &nbsp;&nbsp;→ <a href="{PORTFOLIO}">{PORTFOLIO}</a><br>
        GitHub &nbsp;&nbsp;&nbsp;&nbsp;→ <a href="{GITHUB}">github.com/Gopikrish-30</a><br>
        HuggingFace → <a href="{HUGGINGFACE}">huggingface.co/gopi30</a><br>
        LinkedIn &nbsp;&nbsp;→ <a href="{LINKEDIN}">linkedin.com/in/gopi-m</a>
    </div>

    <p>If there are any openings available now or coming up, I'd love to hear about it.</p>

    <div class="sig">
        Thanks,<br>
        <strong style="color:#111; font-size:14px;">Gopi M</strong><br>
        {PHONE} · <a href="mailto:{SENDER_EMAIL}" style="color:#555; border-bottom:1px solid #ddd;">{SENDER_EMAIL}</a>
    </div>

</body>
</html>"""


def body_plain(company: dict, campaign_tier: str) -> str:
    name = company['company_name']

    intro = (
        "I'm Gopi — a 2× national-level hackathon winner and AI/ML engineer focused on building reliable "
        "systems around LLMs, RAG pipelines, and AI agents. I'm reaching out to ask whether you have any "
        f"remote {TARGET_ROLE} openings — internship, part-time, or otherwise."
    )
    experience = (
        "Over the past year I shipped several AI systems: a fine-tuned translation model with 100+ downloads "
        "on HuggingFace, an AI agent for desktop automation that won Best Technical Implementation at "
        "NEOVERSE'26, a safety-aligned LLM fine-tuned on legal data using Constitutional AI and RLAIF, and "
        "a RAG-based research pipeline built for hallucination resistance. I also completed an 8-month ML "
        "engineering internship building computer vision systems and deploying production applications with "
        "Django and React."
    )

    return f"""Hi {name} team,

{intro}

{experience}

My approach: I build complete systems — not just notebooks. Before reaching for an LLM I always ask whether a simpler approach solves the problem — that question alone keeps systems fast, maintainable, and cheap to run.

Portfolio:    {PORTFOLIO}
GitHub:       {GITHUB}
HuggingFace:  {HUGGINGFACE}
LinkedIn:     {LINKEDIN}

If there are any openings available now or coming up, I'd love to hear about it.

Thanks,
Gopi M
{PHONE} · {SENDER_EMAIL}
"""


# ─── SENDING LOGIC ────────────────────────────────────────────────────────────

def load_sent_log() -> set[str]:
    if Path(LOG_PATH).exists():
        with open(LOG_PATH, 'r') as f:
            data = json.load(f)
        return set(data.get('sent_emails', []))
    return set()


def save_sent_log(sent: set[str]) -> None:
    data = {
        'sent_emails': list(sent),
        'count': len(sent),
        'last_updated': datetime.now().isoformat(),
    }
    with open(LOG_PATH, 'w') as f:
        json.dump(data, f, indent=2)


def build_message(company: dict, campaign_tier: str) -> MIMEMultipart:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject(company, campaign_tier)
    msg['From']    = f"{SENDER_NAME} <{SENDER_EMAIL}>"
    msg['To']      = company['email']
    msg['Reply-To'] = SENDER_EMAIL

    msg.attach(MIMEText(body_plain(company, campaign_tier), 'plain'))
    msg.attach(MIMEText(body_html(company, campaign_tier),  'html'))
    return msg


def send_emails(companies: list[dict], campaign_tier: str, dry_run: bool = False) -> None:
    sent = load_sent_log()
    to_send = [c for c in companies if c['email'] not in sent]

    log.info(f"Companies targeted: {len(companies)} | Already sent: {len(sent)} | To send: {len(to_send)}")

    if dry_run:
        log.info("=== DRY RUN — showing first 3 emails ===")
        for c in to_send[:3]:
            print("\n" + "="*70)
            print(f"TO:      {c['email']}")
            print(f"COMPANY: {c['company_name']} ({c['location']})")
            print(f"SUBJECT: {subject(c, campaign_tier)}")
            print("-"*70)
            print(body_plain(c, campaign_tier))
        return

    if GMAIL_APP_PWD == "xxxx xxxx xxxx xxxx":
        log.error("❌ Set your GMAIL_APP_PWD before sending!")
        sys.exit(1)

    log.info("Connecting to Gmail SMTP...")
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(SENDER_EMAIL, GMAIL_APP_PWD)
        log.info("✅ Logged in. Starting send loop...")

        for i, company in enumerate(to_send, 1):
            try:
                msg = build_message(company, campaign_tier)
                server.sendmail(SENDER_EMAIL, company['email'], msg.as_string())
                sent.add(company['email'])
                log.info(f"[{i}/{len(to_send)}] ✅ Sent → {company['company_name']:<35} {company['email']}")

                # Save progress every 10 emails
                if i % 10 == 0:
                    save_sent_log(sent)

                # Batch pause
                if i % BATCH_SIZE == 0:
                    log.info(f"⏸  Batch pause {BATCH_PAUSE}s after {i} emails...")
                    time.sleep(BATCH_PAUSE)
                else:
                    time.sleep(DELAY_SECONDS)

            except smtplib.SMTPRecipientsRefused:
                log.warning(f"[{i}] ⚠️  Rejected: {company['email']}")
            except smtplib.SMTPException as e:
                log.error(f"[{i}] ❌ SMTP error for {company['email']}: {e}")
                save_sent_log(sent)
                time.sleep(30)  # back off on errors
            except Exception as e:
                log.error(f"[{i}] ❌ Unexpected error: {e}")

        save_sent_log(sent)
        log.info(f"\n🎉 Done! Total sent this session: {len(to_send)} | All-time sent: {len(sent)}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='Gopi Cold Email Bot')
    parser.add_argument('--mode',  choices=['dry_run', 'send', 'resume', 'stats'],
                        default='dry_run', help='Operation mode')
    parser.add_argument('--tier',  choices=['ai', 'tech', 'all'],
                        default='ai', help='Which companies to target')
    parser.add_argument('--csv',   default=CSV_PATH, help='Path to CSV file')
    args = parser.parse_args()

    csv_path = resolve_csv_path(args.csv)
    companies = load_companies(csv_path, args.tier)

    if args.mode == 'stats':
        sent = load_sent_log()
        print(f"\n📊 Stats")
        print(f"  Total companies ({args.tier}): {len(companies)}")
        print(f"  Already sent:                  {len(sent)}")
        print(f"  Remaining:                     {len(companies) - len(sent & {c['email'] for c in companies})}")
        return

    if args.mode in ('send', 'resume', 'dry_run'):
        send_emails(companies, args.tier, dry_run=(args.mode == 'dry_run'))


if __name__ == '__main__':
    main()
