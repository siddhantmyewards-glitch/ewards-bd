---
name: lead-gen
description: Find companies and people on LinkedIn for eWards partnership outreach. Use when asked to find leads, prospects, companies, salespeople, POS vendors, retail consultants, Shopify agencies, marketing agencies, franchise consultants, or any business contacts in a specific city. Outputs a clean XLSX with two sheets - Companies and People.
---

# eWards Lead Generation Skill

You find companies and employees for eWards partnership development. You output verified leads to a Google Sheet.

**Output columns:** Company Name | Vertical / Nature | Website URL | Person Name | Designation | Person LinkedIn

> **First-time setup on a new machine:** see [`SETUP.md`](SETUP.md). It covers Python deps, Camoufox browser fetch, Google Sheets service-account credentials, and the one-time LinkedIn login. Skip this section once setup is done.

## Critical Rules

1. **NEVER fabricate data.** Every URL, name, and designation must come from a real search result or a LinkedIn page you visited. If you didn't see it, it doesn't go in the sheet.
2. **NEVER construct LinkedIn URLs from name patterns.** Only use URLs extracted from LinkedIn pages by the script.
3. **If a field is unknown, leave it blank.** A blank cell is better than a wrong one.
4. **Designations MUST be verified.** The People tab listing shows self-reported headlines that are often vague or misleading. The ONLY source of truth for a person's actual role is the **Experience section** on their individual profile page. Every lead in the output must have a designation verified by visiting their profile.
5. **NEVER skip the city filter.** Every search (role filters AND keyword searches) must have the city/location filter applied. Without it, you get people from all locations which is useless.
6. **Use existing data first.** If prior search results already surfaced high-value leads (e.g., co-founders, directors), go directly to their profiles. Don't re-run the entire search from scratch.

## Target People (ICP)

Only collect people matching these roles:
- **BD / Business Development** (Manager, Head, VP, etc.)
- **Customer Success** (Manager, Head, etc.)
- **Sales** (Manager, Head, VP, etc.)
- **C-suite / Leadership** (Founder, Co-Founder, CEO, MD, Director, CTO, COO) -- especially for companies with <100 employees
- Minimum **2+ years of experience** in the role

**NEVER collect**: designers, QA leads, engineers, office managers, HR, marketing, content creators, or any non-BD/Sales/CS/Leadership roles. These are useless for partnership outreach.

See `references/company.md` for eWards ICP details, current partner lists, and employee targeting rules.

## Company Search Priority (STRICT ORDER)

1. **Retail POS / Retail Tech** -- highest value. POS software, retail ERP, retail billing, retail analytics, omnichannel retail platforms.
2. **Marketing / Consulting companies with retail clients** -- marketing agencies, CRM agencies, Shopify/eCommerce agencies, retail consultants, loyalty platforms that serve retail brands.
3. **F&B / Restaurant POS** -- still valuable but lower priority than retail.

Always process retail-focused companies first.

## Vertical Classification — POS vs Non-POS (CRITICAL)

Before adding any company to the list, verify its **core product** matches the requested vertical. Misclassifying a company wastes page loads and pollutes the sheet.

### What IS a POS company (New POS vertical)

The core product **processes in-store billing transactions**. It is the software/hardware that sits at the cash register / billing counter in a physical retail or F&B outlet.

**Core POS functions:** Checkout / billing, invoice generation, store-level inventory, payment processing, customer-facing transaction handling, receipt printing.

**Examples of POS companies:** Ginesys (Retail ERP + POS), PetPooja (Restaurant POS), Posist (Restaurant POS), GoFrugal (Retail POS), QueueBuster (Mobile POS), Logic ERP (Retail ERP + POS), Wondersoft (Retail POS), RanceLab (F&B POS), Invoay (Retail POS + CRM).

**Subtypes that count as POS:**
- Retail POS / Billing software
- Restaurant / F&B POS / KOT systems
- Retail ERP with a POS module (Ginesys, Logic ERP)
- Mobile POS / mPOS (QueueBuster)
- Cloud POS (EazyCloud)

### What is NOT a POS company

These are **Third-Party Vendors** or other verticals — NOT POS:

| Company Type | What They Do | Why NOT POS |
|---|---|---|
| **OMS / Order Management** (e.g., Vinculum, Unicommerce) | Manage orders across e-commerce channels, warehouse, fulfillment | Handles e-commerce order routing, not in-store billing |
| **E-commerce Platforms** (e.g., Shopify, Tenovia) | Online store builders, e-commerce growth | Sell online, not at a physical counter |
| **Logistics / Shipping** (e.g., Shiprocket, Delhivery) | Package delivery, shipping aggregation | Move packages, don't process sales |
| **Marketing Tech** (e.g., SingleInterface, WebEngage) | Local listings, marketing automation, customer engagement | Marketing tools, not billing software |
| **Messaging / Communication** (e.g., WATI, Gupshup) | WhatsApp/SMS business messaging | Communication channel, not POS |
| **Checkout Optimization** (e.g., GoKwik) | Reduce cart abandonment on e-commerce | Online checkout, not in-store billing |
| **Payment Gateways** (e.g., Razorpay, Pine Labs) | Process digital payments | Payment infra, not full POS software |
| **Analytics / BI** (e.g., iCube) | Business intelligence, data analysis | Reporting layer, not transaction processing |

### The Litmus Test

Ask: **"Does this company's PRIMARY product generate a bill at a physical store counter?"**
- YES → POS ✅
- NO → Classify correctly (Third-Party, E-commerce Tech, Marketing Tech, Logistics, etc.)

**When in doubt:** Check the company's website or LinkedIn "About" section. Look for keywords like "billing", "point of sale", "POS", "retail billing", "restaurant management system", "KOT". If instead you see "order management", "fulfillment", "e-commerce", "marketing automation", "shipping" — it's NOT POS.

## Browser Setup: Camoufox Anti-Detect Browser

All LinkedIn browsing uses **Camoufox** -- an anti-detect browser based on Firefox that prevents LinkedIn from detecting bot activity. Setup is described in [`SETUP.md`](SETUP.md); this section covers how the script uses it at runtime.

**Default paths (override via env vars in `.env`):**
- Binary: bundled with the `camoufox` Python package, downloaded once via `python -m camoufox fetch`. Override with `EWARDS_CAMOUFOX_EXE` only if you have a hand-installed binary.
- Profile/session data: `~/.ewards-lead-gen/camoufox_profile/` (cross-platform). Override with `EWARDS_CAMOUFOX_PROFILE`.
- Saved fingerprint: `<profile>/fingerprint.json`.
- Fingerprint OS: auto-detected from your machine. Override with `EWARDS_CAMOUFOX_OS` (`windows` | `macos` | `linux`).

**How it works:**
- Camoufox generates a random browser fingerprint (fonts, screen size, user-agent, etc.)
- The fingerprint is saved to JSON on first run and reused on every subsequent launch via `from_options` parameter
- This is critical: if the fingerprint changes between launches, LinkedIn invalidates the session cookies and you have to log in again
- `persistent_context=True` saves cookies/session between launches
- Both fixed fingerprint + persistent context = session survives across script runs

**Before every script run, always:**
1. Kill any zombie Camoufox processes:
   - Windows: `powershell -Command "Get-Process camoufox -ErrorAction SilentlyContinue | Stop-Process -Force"`
   - macOS / Linux: `pkill -f camoufox || true`
2. Remove stale lock files from the profile dir:
   - Windows: `rm -f "$HOME/.ewards-lead-gen/camoufox_profile/parent.lock" "$HOME/.ewards-lead-gen/camoufox_profile/.parentlock" "$HOME/.ewards-lead-gen/camoufox_profile/lock"`
   - macOS / Linux: same command, `$HOME` resolves correctly
   - If `EWARDS_CAMOUFOX_PROFILE` is set, use that path instead.

**If the browser can't launch** (exitCode=0 error), it's always a zombie process or stale lock. Kill processes and remove locks.

**If the session is lost** (redirects to /login), the user must log in manually. The script opens the login page and waits up to 5 minutes for the user to complete login. Cookies persist in the profile dir for future runs.

## Execution Flow

### Step 0: Always Ask First

Every time /lead-gen is triggered, start fresh. Present options:

**1. City?**
Options: Delhi NCR | Mumbai | Bangalore | Chennai | Hyderabad | Pune | Kolkata | (or custom)

**2. Vertical?**
Options: Current POS | New POS | Current Third-Party Vendors | New Third-Party Vendors | Individual Referrals | Channel Distributors

**3. How many leads?** (default: 30)

Wait for answers before proceeding.

### Step 1: Parse the Response

Extract:
- **Company type** -- derived from vertical
- **City** -- the selected city
- **Volume** -- how many leads (default: 30)

**Current Third-Party Vendors shortcut:** Company list is pre-known (Shiprocket, WATI, SPUR, GoKwik, Smartping). Skip Step 2 and go straight to Step 3.

### Step 2: Find Company Names (Web Search)

Use WebSearch ONLY to discover company names, websites, and verticals. **NEVER use web search to find people.**

#### Layer 1: Broad Discovery (3-5 searches)
- `"{company type}" "{city}" -linkedin`
- `"{company type}" "{city}" contact OR website`
- `site:linkedin.com/company "{company type}" "{city}"`

#### Layer 2: Mine Directory Sites
Go deeper than page-1 Google results. Search POS/billing/retail category pages on these directories:
- **SoftwareSuggest** — `site:softwaresuggest.com "{company type}" "{city}"`
- **Capterra India** — `site:capterra.in "POS" OR "billing" OR "retail"`
- **TechJockey** — `site:techjockey.com "{company type}"`
- **G2** — `site:g2.com "{company type}" India`
- **IndiaMART** — `site:indiamart.com "{company type}" "{city}"` (supplier/manufacturer listings)
- **Tracxn** — `site:tracxn.com "{company type}" "{city}"`
- **Clutch** — `site:clutch.co "{company type}" India`

These directories list 50-100+ companies per category. Many won't appear in generic Google searches.

#### Layer 3: Competitor / Alternative Lists
Search competitor and alternative lists for existing eWards partners to surface companies competing in the same space:
- `"{existing partner}" alternatives India` (e.g., "Ginesys alternatives India", "GoFrugal competitors")
- `"{existing partner}" vs` (e.g., "PetPooja vs", "Wondersoft vs")
- `"best alternatives to {existing partner}"` 

Run these for 3-5 of the largest existing partners relevant to the target vertical.

#### Compile & Classify
For each company found:
1. Capture its **vertical / nature** (3-5 words: "Retail POS / ERP", "Loyalty Platform", "F&B Consulting")
2. **Apply the Litmus Test** from the Vertical Classification section — confirm the core product matches the requested vertical
3. **Check against the 54 existing partner list** in `references/company.md` — exclude any already partnered
4. **Order by priority:** Retail Tech first, Marketing/Consulting second, F&B third

### Step 2A: Confirm Company List with User (MANDATORY)

**NEVER run the LinkedIn script without user approval on the company list.**

Present the compiled company list to the user using `AskUserQuestion` with `multiSelect: true`. Group companies by sub-vertical (e.g., Retail POS, F&B POS). Each option MUST include:
- **Label:** Company name
- **Description:** What they do (1 line — core product, location, size if known, website)

Wait for the user to select which companies they want leads for. Only proceed with the selected companies.

### Step 2B: Validate Company LinkedIn Slugs

Before searching people, validate each company's LinkedIn page via web search.

**Primary method — Google search:**
1. Search: `site:linkedin.com/company "{company name}"`
2. Also try: `"{company name}" linkedin.com/company`
3. Verify: name matches, industry matches, location matches
4. Record the validated slug (e.g., `ginesys`, `storehub`)

**Fallback — Search on LinkedIn directly:**
If Google doesn't return the company page, search on LinkedIn itself:
1. Navigate to `https://www.linkedin.com/search/results/companies/?keywords={full company name}` in Camoufox
2. Find the matching company from the search results
3. Extract the slug from the URL

**NEVER skip the fallback.** Many smaller companies don't appear in Google's site: search but DO have LinkedIn company pages. Always try both methods before declaring a company has no LinkedIn page.

**NEVER guess slugs.** A wrong slug wastes page loads and returns irrelevant people.

### Step 3: Find People (LinkedIn via Camoufox)

This is the core step. Use `scripts/linkedin_search.py` which handles Camoufox browser, rate limiting, and profile parsing.

**Command:**
```bash
PYTHONIOENCODING=utf-8 python scripts/linkedin_search.py \
  --companies "CompanyA:slug-a,CompanyB:slug-b" \
  --city "Delhi NCR" \
  --output results.json
```

**What the script does per company (you do NOT need to do any of this manually -- the script handles it all):**

#### Phase 1: Listing Scan (identify who works there)

For each of the three role filters (Sales, Business Development, Customer Success):

1. **Navigate to the company's People tab:** `linkedin.com/company/{slug}/people/`
   - This is a FRESH page load for each role filter. Do NOT try to click/unclick filters on the same page -- the page state becomes stale and subsequent filters return 0 results.
2. **Read the filter sidebar:** Parse "Where they live" (location filters with counts) and "What they do" (role filters with counts) and total employee count.
3. **Click the CITY filter first** from "Where they live" (e.g., "Greater Delhi Area"). This narrows all results to the target city. Without this, you get people from all locations.
4. **Click the ROLE filter second** on top of the city filter (e.g., "Sales"). LinkedIn filters are additive -- city + role together gives you Sales people in Delhi.
5. **Collect all profile links** from the filtered results page (`a[href*="/in/"]` elements).
6. **Visit every profile** from the collected links (see Phase 2 below).

Then for each leadership keyword (Founder, CEO, Director, Head):

1. **Navigate to:** `linkedin.com/company/{slug}/people/?keywords={keyword}`
   - Navigation resets all filters, so the city filter must be re-applied.
2. **Re-click the CITY filter** after the page loads.
3. **Collect all new profile links** (skip any already visited from role filters).
4. **Visit every new profile** (see Phase 2 below).

#### Phase 2: Profile Visits (verify actual designation)

For every profile link collected in Phase 1:

1. **Navigate to the profile URL** (e.g., `linkedin.com/in/john-doe-12345`)
2. **Scroll the page** to load the Experience section
3. **Read the page text** from the `<main>` element
4. **Extract the person's name** (first substantial text line)
5. **Extract the headline** (second substantial text line)
6. **Parse the Experience section:**
   - Find the line that says "Experience"
   - Read entries until hitting "Education", "Skills", "Certifications", etc.
   - Each experience entry has: Title, Company/Employment type, Date range/Duration
   - The FIRST experience entry is the current role
7. **Record:** name, verified_title (from Experience), org, tenure, headline, LinkedIn URL

**The Experience section is the ONLY source of truth for designations.** The People tab listing shows customizable headlines that are often vague ("He/Him", "Building things", etc.) and do NOT reflect the actual role.

#### Rate Limiting

The script enforces:
- **5-10s random delay** between page navigations
- **5-8s random delay** between profile visits
- **Max 80 page loads** per session
- **Auto-stop** on LinkedIn challenges/captchas
- **Human-like scroll jitter** on every page

#### City Filter Aliases

The script maps city names to LinkedIn's location filter labels:
- "Delhi NCR" -> matches: delhi, new delhi, greater delhi, gurugram, gurgaon, noida, faridabad, ghaziabad, ncr
- "Mumbai" -> matches: mumbai, greater mumbai, navi mumbai, thane
- "Bangalore" -> matches: bangalore, bengaluru, greater bengaluru
- "Southeast Asia" / "SEA" -> matches: malaysia, singapore, indonesia, thailand, philippines, vietnam, kuala lumpur, jakarta, bangkok, manila, etc.

#### What Gets Skipped

- Companies where the People page returns "Page not found"
- Companies with >50 employees where the target city does NOT appear in the location filters
- LinkedIn challenges/captchas (script stops immediately)
- Duplicate profile links (tracked across all filters and keyword searches within a company)
- Duplicate names in final output

### Step 4: Deduplicate

- Two company records match if names are very similar (ignore case, punctuation, "Pvt Ltd", "LLP")
- Two people records match if same name + same company
- When merging duplicates, prefer the record with more fields filled
- Check against `references/existing_leads.md` if it exists -- exclude anyone already there

### Step 5: Push to Google Sheet

**Create `merged_leads.json`** with this structure:
```json
{
  "companies": [
    {"name": "Ginesys", "vertical": "Retail POS / ERP", "website": "ginesys.in", "linkedin": ""}
  ],
  "people": [
    {"name": "Sapna Sharma", "designation": "Inside Sales Manager", "linkedin": "https://linkedin.com/in/sapna-sharma-6b8326147", "company": "Ginesys"}
  ],
  "metadata": {
    "company_focus": "POS",
    "city": "Delhi NCR"
  }
}
```

**The `designation` field in merged_leads.json must use the `verified_title` from the profile visit, NOT the listing headline.**

**Push to Google Sheets:**
```bash
python scripts/push_to_gsheet.py --input merged_leads.json --sheet-id "$GSHEET_ID"
```

`GSHEET_ID` is read from `.env` in the skill folder. Default sheet (eWards working sheet): `GSHEET_ID=1NEszZSx42QJ5-x5qCsZm4-2rMpUD1dWeGq62n5BVv3s`. The push script also takes `--cred` (defaults to `gsheets_cred.json` in the working directory — the service-account key, see `SETUP.md`).

This creates a new tab with columns: Company Name | Vertical / Nature | Website URL | Person Name | Designation | Person LinkedIn

**Fallback to local XLSX:**
```bash
python scripts/generate_xlsx.py --input merged_leads.json --output leads_{type}_{city}_{date}.xlsx
```

### Step 6: Report

Tell the user:
- Total companies searched
- Total verified leads found
- Breakdown by filter source (Sales, BD, CS, Leadership)
- The Google Sheet link (clickable)
- Any companies that were skipped and why

Do NOT add email guesses, outreach templates, priority scores, or any other columns. The user qualifies the leads themselves.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| "Failed to launch browser process" | Zombie Camoufox process or stale lock file | Kill processes + remove locks (see Browser Setup) |
| Session lost (redirects to /login) | Fingerprint changed or cookies expired | User must log in manually in the browser window |
| BD/CS filter returns 0 results | Stale page state from previous filter | Script already handles this: fresh page load per role filter |
| "charmap codec" error loading fingerprint | Unicode font names in JSON | Script uses `encoding='utf-8'` (already handled) |
| Profile parsing returns company name as title | Experience section has company as first line, not role | Known edge case with LinkedIn's format -- headline is used as fallback |
| Rate limit hit mid-run | >80 page loads in one session | Script stops automatically. Run again for remaining companies. |
