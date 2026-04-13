---
name: lead-gen
description: Find companies and people on LinkedIn for eWards partnership outreach. Use when asked to find leads, prospects, companies, salespeople, POS vendors, retail consultants, Shopify agencies, marketing agencies, franchise consultants, or any business contacts in a specific city. Outputs a clean XLSX with two sheets - Companies and People.
---

# eWards Lead Generation Skill

You find companies and employees for eWards partnership development. You output a clean XLSX with two sheets:

**Columns:** Company Name | Vertical / Nature | Website URL | Company LinkedIn | Person Name | Designation | Person LinkedIn

## Critical Rules

1. **NEVER fabricate data.** Every URL, name, and designation must come from an actual search result or fetched webpage. If you didn't see it in a result, it doesn't go in the sheet.
2. **NEVER construct LinkedIn URLs from name patterns.** The URL `linkedin.com/in/firstname-lastname` is a guess, not a fact. Only use URLs that appeared in search results.
3. **If a field is unknown, leave it blank.** A blank cell is better than a wrong one.

## Target People (ICP)

Only collect people matching these roles:
- **BD / Business Development** (Manager, Head, VP, etc.)
- **Customer Success** (Manager, Head, etc.)
- **Sales** (Manager, Head, VP, etc.)
- **C-suite / Leadership** (Founder, Co-Founder, CEO, MD, Director, CTO, COO) — especially for companies with <100 employees
- Minimum **2+ years of experience** in the role

**NEVER collect**: designers, QA leads, engineers, office managers, HR, marketing, content creators, or any non-BD/Sales/CS/Leadership roles. These are useless for partnership outreach.

See `references/company.md` for eWards ICP details, current partner lists, and employee targeting rules.

## Execution Flow

### Step 0: Always Ask First

Every time /lead-gen is triggered, **start fresh**. Do NOT carry over context from previous runs. Present clickable options using AskUserQuestion:

**1. City?**
Options: Delhi NCR | Mumbai | Bangalore | Chennai | Hyderabad | Pune | Kolkata

**2. Vertical?**
Options: Current POS | New POS | Current Third-Party Vendors | New Third-Party Vendors | Individual Referrals | Channel Distributors

**3. How many leads?** (default: 30)

Wait for the user to answer before proceeding. Do NOT assume answers from previous conversations.

### Step 1: Parse the Response

From the user's answers, extract:
- **Company type** — derived from the vertical (e.g., "Current POS" -> POS software companies, "Current Third-Party Vendors" -> the 5 existing third-party vendor partners, "New Third-Party Vendors" -> new vendor companies, "Channel Distributors" -> IT distributors/resellers)
- **City** — the selected city
- **Volume** — how many leads they want (default: 30 if not specified)

**Current Third-Party Vendors shortcut:** If the user picks **Current Third-Party Vendors**, the company list is already known — Shiprocket, WATI, SPUR, GoKwik, Smartping (from company.md). **Skip Step 2 entirely** and go straight to Step 3 (LinkedIn people search) using these 5 companies. This works exactly like "Current POS" — the companies are pre-defined, you only need to find people at them in the selected city.

### Step 2: Find Company Names (Web Search)

Use web_search ONLY to discover company names and websites. Do NOT use web search to find people — it produces garbage data.

**Company searches (run 3-5):**
- `"{company type}" "{city}" -linkedin`
- `"{company type}" "{city}" contact OR website`
- `site:linkedin.com/company "{company type}" "{city}"`
- Check directories like IndiaMART, Tracxn, SoftwareSuggest for company lists

For each company, also capture its **vertical / nature** — a short label describing what the company does (e.g., "CPaaS / UCaaS", "POS Software", "Retail Tech", "F&B Consulting", "Loyalty Platform"). This comes from the LinkedIn company page tagline, website, or search snippet. Keep it to 3-5 words max.

**Search priority:** Always prioritize **Retail POS / Retail Tech** companies over restaurant-only or F&B-only POS companies. Retail tech companies are the highest-value targets for eWards partnerships. When ordering the company list for people search, put retail-focused companies first.

Output: a list of company names + verticals + websites (where available).

### Step 3: Find People (LinkedIn via Chrome — Agentic Browsing)

Use Claude in Chrome with the `computer` tool (screenshot + click/type) to scrape people from LinkedIn company pages. This is the ONLY reliable way to get real names, designations, and profile URLs.

**Use agentic browsing (`computer` tool), NOT `read_page`/`navigate` alone.** The computer tool takes screenshots, clicks at coordinates, and types — it handles LinkedIn's dynamic UI (filters, dropdowns, lazy-loaded results) far better than DOM reading.

**Workflow per company:**

1. `navigate` -> `linkedin.com/company/{name}/people/`
2. `computer: wait` 2-3s -> let page load
3. `computer: screenshot` -> see the People tab with filters

**Applying filters:**

4. **City filter** — LinkedIn shows location filter pills/dropdowns on the People tab. Take a screenshot, find the location filter, click it, and select the target city.

5. **Role filters — two strategies:**
   - **Click pre-built filters** for: Sales, Business Development, Customer Success — these are typically available as clickable filter pills on the People tab. Screenshot -> find -> click.
   - **Manually type** in the People search bar ONLY for: Founder, Co-Founder, CEO, MD, Director, CTO, COO, Head — these are NOT available as pre-built filters. Click the search box within People, type the keyword, press Enter.

6. `computer: wait` 2-3s -> let filtered results load
7. `computer: screenshot` -> read the results
8. Extract: **Name**, **Designation**, **LinkedIn Profile URL** (from the profile link visible on the page)
9. Only collect people matching the Target People ICP
10. If more results exist, scroll down and screenshot again
11. `computer: wait` 3-5s -> delay before next company to avoid bot detection

**Important:**
- Always screenshot BEFORE clicking — never guess coordinates
- Click in the CENTER of buttons/links
- If a filter is already visible as a clickable pill, click it — don't type it
- If results show 0 for a filter, move to the next filter keyword, don't waste time

**Chrome connection setup:** If Chrome is not connected, ask the user to:
1. Open Chrome with Claude in Chrome extension
2. Log into LinkedIn (secondary account from ldcred.env)
3. Click "Connect" on the extension
4. Confirm ready

### Step 4: Deduplicate

Deduplication rules:
- Two company records match if their names are very similar (ignore case, punctuation, "Pvt Ltd", "LLP", etc.)
- Two people records match if same name + same company
- When merging duplicates, prefer the record that has more fields filled in

### Step 5: Push to Google Sheet

Create a merged_leads.json with `companies`, `people`, and `metadata` keys. Each company object must include `"vertical"` (the short nature/vertical label).

The metadata should include `"company_focus"` and `"city"` — these auto-generate the tab label.

**Push to Google Sheets (primary):**

```bash
python scripts/push_to_gsheet.py --input merged_leads.json --sheet-id SHEET_ID_FROM_ENV
```

The Google Sheet ID is stored in the project's `gsheets_config.env` file. Read it before running:
- `GSHEET_ID` — the spreadsheet ID from the Google Sheet URL

This creates one new tab in the shared "eWards Leads" Google Sheet with combined company + people data:
- Tab label: `{company_focus}_{city}_{date}` (auto-generated from metadata, or override with `--label`)
- Columns: Company Name | Vertical / Nature | Website URL | Company LinkedIn | Person Name | Designation | Person LinkedIn
- Each row is one person, with their company's details repeated alongside

**Fallback to local XLSX** (if Google Sheets fails or user requests it):

```bash
python scripts/generate_xlsx.py --input merged_leads.json --output leads_{type}_{city}_{date}.xlsx
```

This generates a single "Leads" sheet with the same 7-column layout.

### Step 6: Report

Tell the user:
- Total companies found
- Total people found
- The Google Sheet link (clickable)

Do NOT add email guesses, outreach templates, priority scores, or any other columns. The user qualifies the leads themselves.
