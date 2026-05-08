# Cold Mail Automation

Automate personalized internship outreach to companies in the dataset using Gmail SMTP and a resume-safe sent log.

This repository is designed for legitimate, permission-aware cold outreach. It loads companies from the CSV, filters rows with valid email addresses, personalizes each email, and sends messages in batches with basic throttling and progress tracking.

## What it does

- Reads company records from the dataset CSV.
- Filters active companies with valid contact email addresses.
- Supports three campaign tiers:
  - `all` for the full dataset
  - `ai` for AI/ML-focused companies
  - `tech` for broader tech companies
- Generates a personalized subject line and email body.
- Sends through Gmail SMTP using an app password.
- Saves delivery progress in `sent_log.json` so the run can be resumed safely.

## Dataset summary

The bundled dataset currently contains:

| Metric | Count |
|---|---:|
| Total rows | 6,977 |
| Active rows | 6,933 |
| Active rows with valid email | 5,048 |

## Repository structure

| File | Purpose |
|---|---|
| `cold_email_bot.py` | Main automation script |
| `Canadian Businesses - Sheet1.csv` | Source dataset |
| `README.md` | Project documentation |

## Requirements

- Python 3.10 or newer
- A Gmail account with 2-Step Verification enabled
- A Gmail App Password

No third-party Python packages are required. The script uses only the Python standard library.

## Setup

### 1) Enable Gmail App Passwords

1. Open [myaccount.google.com](https://myaccount.google.com).
2. Go to `Security`.
3. Enable `2-Step Verification` if it is not already enabled.
4. Open `App passwords`.
5. Create a new password for Mail.
6. Copy the 16-character app password.

### 2) Configure the script

Open `cold_email_bot.py` and provide values through environment variables before running the script:

```python
SENDER_NAME   = os.getenv("SENDER_NAME", "")
SENDER_EMAIL  = os.getenv("SENDER_EMAIL", "")
GMAIL_APP_PWD = os.getenv("GMAIL_APP_PWD", "")
```

Set those variables in your shell or editor before running the script.

### 3) Keep the CSV in the project folder

Make sure the dataset file is in the same directory as the script:

```text
cold_email_bot.py
Canadian Businesses - Sheet1.csv
README.md
```

## Usage

Run the script from the project directory.

### Dry run

Preview the first few messages without sending anything:

```bash
python cold_email_bot.py --mode dry_run --tier all
```

### Send mode

Send emails to the full dataset:

```bash
python cold_email_bot.py --mode send --tier all
```

Send only AI/ML-focused companies:

```bash
python cold_email_bot.py --mode send --tier ai
```

Send only tech-focused companies:

```bash
python cold_email_bot.py --mode send --tier tech
```

### Stats

Check how many emails are left to send:

```bash
python cold_email_bot.py --mode stats --tier all
```

### Resume

If the process was interrupted, rerun it and the script will skip addresses already stored in `sent_log.json`:

```bash
python cold_email_bot.py --mode resume --tier all
```

## How the automation works

1. Loads the CSV using `csv.DictReader`.
2. Keeps only rows with a valid `contact_email`.
3. Keeps only rows where `operating_status` is `active`.
4. Builds a company record with the company name, email, location, website, LinkedIn, and category data.
5. Creates a subject and message body for the selected campaign tier.
6. Sends the email through Gmail SMTP over SSL.
7. Stores sent addresses in `sent_log.json` for resume support.

## Email content

Current outreach copy is aimed at AI Engineer Internship and ML Engineer Internship roles.

### Subject line

```text
AI Engineering Internship Enquiry
```

### Body preview

```text
Hi {company_name} team,

I'm reaching out to ask whether you have any remote AI Engineer Internship / ML Engineer Internship openings — internship, part-time, or otherwise.

The work I have done includes AI systems, automation tools, and production web applications, with experience in LLMs, RAG pipelines, computer vision, and deployment workflows.

My approach: I build complete systems — not just notebooks. Before reaching for an LLM I always ask whether a simpler approach solves the problem — that question alone keeps systems fast, maintainable, and cheap to run.

If there are any openings available now or coming up, I'd love to hear about it.
```

## Output files

The script may create these files during a run:

| File | Purpose |
|---|---|
| `sent_log.json` | Stores sent email addresses so runs can resume |
| `email_bot.log` | Detailed timestamped run log |

## Sending behavior

- Emails are throttled with an 8-second delay between sends.
- A longer pause is inserted every 50 emails.
- Errors are logged so a run can be resumed later.

## Customization

You can customize the campaign by editing these values in `cold_email_bot.py`:

- `SENDER_NAME`
- `SENDER_EMAIL`
- `GMAIL_APP_PWD`
- `TARGET_ROLE`

You can also adjust the AI and tech keyword lists if you want to change targeting logic.

## Troubleshooting

### Gmail login fails

- Confirm that 2-Step Verification is enabled.
- Confirm that the app password was pasted exactly.
- Make sure the app password is not a regular Gmail password.

### No companies appear in dry run

- Confirm the CSV file is named `Canadian Businesses - Sheet1.csv`.
- Confirm the CSV is in the same folder as the script.
- Check that the `contact_email` values are valid.

### Script resumes but skips too much

- The sent log is intentionally resume-safe.
- Delete `sent_log.json` only if you want to start a fresh campaign.

## Suggested workflow

1. Run a dry run with `--mode dry_run --tier all`.
2. Review the first few rendered emails.
3. Run `--mode send --tier all` when ready.
4. Check progress with `--mode stats --tier all`.
5. Resume later with `--mode resume --tier all` if needed.

## Notes

- This project is intended for legitimate outreach only.
- Respect email laws, company policies, and recipient preferences.
- Keep send volume conservative to reduce the chance of deliverability issues.