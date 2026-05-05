# lead-gen — One-time Setup

Follow these steps once on a new machine. After this, running `/lead-gen` in Claude Code Just Works.

---

## 1. Prerequisites

- **Python 3.10+** (`python --version`)
- **git** (only if you cloned this repo)
- A **Google account** with access to a Google Sheet you want leads pushed to
- A **LinkedIn account** (a working personal one — you'll log in manually once)

Works on Windows, macOS, and Linux. All paths in this skill are configurable via env vars and default to OS-appropriate locations.

---

## 2. Install Python dependencies

From inside the skill folder (`skills/lead-gen/`):

```bash
pip install -r requirements.txt
```

This installs:
- `camoufox` — the anti-detect browser (Firefox fork) used for LinkedIn scraping
- `playwright` — used by Camoufox under the hood
- `gspread` + `google-auth` — for pushing leads to Google Sheets
- `openpyxl` — fallback XLSX export

---

## 3. Download the Camoufox browser binary

Camoufox is a real browser (not just a Python package). Run this once:

```bash
python -m camoufox fetch
```

It downloads ~200 MB into the `camoufox` Python package's data directory. You will not need to manage `C:/camoufox_bin/` or any custom path — the package finds its own browser. (If you *do* have a hand-installed Camoufox somewhere weird, set `EWARDS_CAMOUFOX_EXE=/path/to/camoufox` in `.env`.)

---

## 4. Configure environment

```bash
cp .env.example .env
```

Open `.env` and set at minimum:

```
GSHEET_ID=<your-google-sheet-id>
```

You get the sheet ID from your sheet's URL: `https://docs.google.com/spreadsheets/d/THIS_PART_HERE/edit`.

The Camoufox profile location defaults to `~/.ewards-lead-gen/camoufox_profile/` and works without any further config.

---

## 5. Set up Google Sheets credentials

The skill writes leads via a **Google Cloud service account**.

1. Go to https://console.cloud.google.com/ and create (or pick) a project.
2. Enable the **Google Sheets API** and **Google Drive API**.
3. Go to **IAM & Admin → Service Accounts → Create service account**. Give it any name.
4. After creation, open the service account → **Keys → Add Key → JSON**. Download the JSON file.
5. Save the JSON as `gsheets_cred.json` inside the skill folder. (It is `.gitignore`d — never commit it.)
6. Open the downloaded JSON, copy the `client_email` field (looks like `xxx@yyy.iam.gserviceaccount.com`).
7. Open your Google Sheet → click **Share** → paste that email and give it **Editor** access.

That's it — your service account can now read/write that sheet.

---

## 6. First-time LinkedIn login

The very first time you run `/lead-gen`, Camoufox will detect that you are not logged into LinkedIn and open the login page. Sign in manually in the browser window that pops up. The session cookies persist in `~/.ewards-lead-gen/camoufox_profile/`, so future runs reuse the same login.

If LinkedIn ever logs you out (rare — usually only after fingerprint changes), the script will re-prompt automatically.

---

## 7. Try it

In Claude Code:

```
/lead-gen
```

Pick a city, vertical, and lead count. Claude will run the search and push to your sheet.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ERROR: camoufox not installed` | `pip install -r requirements.txt` |
| `Failed to launch browser process` | Browser binary not fetched. Run `python -m camoufox fetch`. |
| Stale lock files block launch | Delete `parent.lock`, `.parentlock`, `lock` from your profile dir. |
| Session keeps redirecting to /login | Fingerprint changed — log in once more, it'll persist. |
| `gspread.exceptions.SpreadsheetNotFound` | The service account doesn't have access to the sheet. Share the sheet with the service account email (Editor access). |
| `PermissionError` on profile dir | Pick a writable path via `EWARDS_CAMOUFOX_PROFILE=/your/path` in `.env`. |
