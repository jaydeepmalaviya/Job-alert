# 📊 Daily Job Alert Agent
**Monitors 60+ Toronto & Halifax asset management / fund administration career pages and emails you new postings every morning — for FREE using GitHub Actions.**

---

## How It Works

```
Every weekday at 7 AM EST
        │
        ▼
GitHub Actions wakes up (free cloud runner)
        │
        ▼
Scrapes all 60+ career pages
(Greenhouse API, Lever API, Workday, HTML)
        │
        ▼
Compares against seen_jobs.json (job history)
        │
        ▼
Sends you a beautiful HTML email digest via Gmail
        │
        ▼
Saves updated job history back to repo
```

---

## ⚙️ One-Time Setup (15 minutes)

### STEP 1 — Create a GitHub Account (if you don't have one)
Go to **https://github.com/signup** — it's free.

---

### STEP 2 — Create a New GitHub Repository

1. Go to **https://github.com/new**
2. Name it: `job-alert-agent` (or anything you like)
3. Set it to **Private** ✅ (keeps your email address secret)
4. Click **Create repository**

---

### STEP 3 — Upload the Agent Files

Upload all files from this folder to your new repo, keeping the folder structure:

```
your-repo/
├── job_agent.py
├── requirements.txt
├── data/
│   └── seen_jobs.json          ← start empty: just contains {}
└── .github/
    └── workflows/
        └── daily_job_alert.yml
```

**Easy way to upload:**
1. On your new repo page, click **"uploading an existing file"**
2. Drag and drop all the files
3. Click **Commit changes**

> ⚠️ Make sure `.github/workflows/daily_job_alert.yml` is uploaded — GitHub needs this exact path.

---

### STEP 4 — Create a Gmail App Password

> This is a special 16-character password just for the agent. It is **NOT** your regular Gmail password.
> You can revoke it at any time from your Google Account settings.

1. Go to your Google Account: **https://myaccount.google.com**
2. Click **Security** in the left sidebar
3. Under "How you sign in to Google", click **2-Step Verification** (enable it if not already on)
4. Scroll to the bottom → click **App passwords**
5. Under "App name" type: `Job Alert Agent`
6. Click **Create**
7. Google shows you a **16-character password** like `abcd efgh ijkl mnop`
8. **Copy it immediately** — you won't see it again

---

### STEP 5 — Add Secrets to GitHub

Your Gmail credentials are stored as encrypted GitHub Secrets — they are never visible in code.

1. Go to your repo on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these 3 secrets:

| Secret Name | Value |
|---|---|
| `GMAIL_SENDER` | Your Gmail address (e.g. `yourname@gmail.com`) |
| `GMAIL_APP_PASSWORD` | The 16-char app password from Step 4 (no spaces) |
| `RECIPIENT_EMAIL` | Email address to RECEIVE the daily digest (can be same as sender) |

---

### STEP 6 — Test It Manually

Before waiting until tomorrow morning, trigger a manual run:

1. Go to your repo → click **Actions** tab
2. Click **Daily Job Alert Agent** in the left sidebar
3. Click **Run workflow** → **Run workflow** (green button)
4. Watch the run — it takes 2–5 minutes
5. Check your inbox! 🎉

---

### STEP 7 — Adjust the Schedule (Optional)

The default schedule is **Monday–Friday at 7:00 AM Toronto time (EST)**.

To change the time, edit `.github/workflows/daily_job_alert.yml`:

```yaml
- cron: "0 12 * * 1-5"
```

The format is: `minute hour day month day-of-week` (all in UTC)

| You want | Cron value |
|---|---|
| 7 AM EST (Mon–Fri) | `0 12 * * 1-5` |
| 8 AM EST (Mon–Fri) | `0 13 * * 1-5` |
| 7 AM EDT / summer  | `0 11 * * 1-5` |
| 7 AM every day     | `0 12 * * *`   |

---

## 📧 What the Email Looks Like

```
Subject: 🆕 Job Alert: 14 new posting(s) — Jan 15, 2026

┌─────────────────────────────────────────────────┐
│           📊 Daily Job Alert                    │
│         Wednesday, January 15, 2026             │
├─────────────────────────────────────────────────┤
│   🎉 14 new job postings found                  │
├─────────────────────────────────────────────────┤
│ 📍 TORONTO                                      │
│                                                  │
│ 🏢 CPP Investments                              │
│   Senior Portfolio Manager – Infrastructure     │
│                                                  │
│ 🏢 Brookfield Asset Management                  │
│   Associate, Private Equity                     │
│                                                  │
│ 📍 HALIFAX                                      │
│                                                  │
│ 🏢 Citco Fund Services                         │
│   Fund Accountant – Hedge Funds                 │
└─────────────────────────────────────────────────┘
```

- Each job title is a **clickable link** to apply directly
- Only **NEW postings** are shown — no repeated jobs
- If nothing new: you get a quiet "no new postings today" email

---

## 🔧 Customization

### Add or remove companies
Edit the `COMPANIES` list in `job_agent.py`. Each entry is:
```python
("Company Name", "City", "https://careers-url.com", "ats_type"),
```
`ats_type` options: `"greenhouse"`, `"lever"`, `"workday"`, `"html"`

### Change monitored cities
Remove any lines in `COMPANIES` for cities you don't want.

### Run on weekends too
Change `1-5` to `*` in the cron expression.

### Reset job history (re-scan all jobs)
Delete the contents of `data/seen_jobs.json` and replace with `{}`, then commit.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| No email received | Check GitHub Actions log for errors; verify Secrets are set correctly |
| Gmail authentication error | Regenerate App Password in Google Account settings |
| "Permission denied" on git push | Ensure workflow has `permissions: contents: write` (already set) |
| Too many emails / spam | The agent only emails NEW jobs. If flooded on day 1, that's normal — it'll calm down |
| Some companies show no jobs | Some career pages are heavily JavaScript-rendered; the agent will keep checking |

---

## 💰 Cost

| Service | Cost |
|---|---|
| GitHub Actions | **Free** (2,000 minutes/month free — agent uses ~3 min/day) |
| Gmail SMTP | **Free** |
| Total | **$0/month** |

---

## 📁 File Structure

```
job-alert-agent/
│
├── job_agent.py               # Main agent: scrapes + emails
├── requirements.txt           # Python dependencies
│
├── data/
│   └── seen_jobs.json         # Auto-updated job history (do not edit manually)
│
└── .github/
    └── workflows/
        └── daily_job_alert.yml  # GitHub Actions schedule & runner config
```
