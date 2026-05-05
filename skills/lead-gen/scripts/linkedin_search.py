#!/usr/bin/env python3
"""
LinkedIn Lead Search — Filter + Visit approach:
  1. Apply LinkedIn's built-in filters (Sales, BD, CS) or keyword searches
  2. Visit every profile from the filtered results
  3. Read Experience section for verified title

Usage:
    python scripts/linkedin_search.py --companies "StoreHub:storehub" --city "Southeast Asia" --output results.json
"""

import argparse
import json
import os
import platform
import random
import re
import sys
import time
from pathlib import Path

try:
    from camoufox.sync_api import Camoufox
    from camoufox.utils import launch_options as cfx_launch_options
except ImportError:
    print("ERROR: camoufox not installed. Run: pip install -r requirements.txt && python -m camoufox fetch")
    sys.exit(1)

# --- Configurable paths (override via env vars; sensible defaults work on any OS) ---
# Profile dir holds the Camoufox session (cookies, saved fingerprint).
# Default: ~/.ewards-lead-gen/camoufox_profile/  -- override with EWARDS_CAMOUFOX_PROFILE.
USER_DATA_DIR = os.environ.get("EWARDS_CAMOUFOX_PROFILE") or str(
    Path.home() / ".ewards-lead-gen" / "camoufox_profile"
)
FINGERPRINT_FILE = str(Path(USER_DATA_DIR) / "fingerprint.json")

# Camoufox binary: leave unset to let the camoufox package use its bundled browser
# (downloaded once via `python -m camoufox fetch`). Override with EWARDS_CAMOUFOX_EXE
# only if you have a hand-installed binary at a custom path.
CAMOUFOX_EXE = os.environ.get("EWARDS_CAMOUFOX_EXE") or None

# Fingerprint OS: auto-detect, override with EWARDS_CAMOUFOX_OS (windows | macos | linux).
_PLATFORM_MAP = {"Windows": "windows", "Darwin": "macos", "Linux": "linux"}
CAMOUFOX_OS = os.environ.get("EWARDS_CAMOUFOX_OS") or _PLATFORM_MAP.get(platform.system(), "windows")

MAX_LOADS = 80
DELAY_PAGE = (5, 10)
DELAY_PROFILE = (5, 8)
_loads = 0


def go(page, url, delay_range=DELAY_PAGE):
    global _loads
    if _loads >= MAX_LOADS:
        print(f"  [RATE LIMIT] Hit {MAX_LOADS} loads.", flush=True)
        return False
    if _loads > 0:
        d = random.uniform(*delay_range)
        print(f"  [WAIT {d:.0f}s]", flush=True)
        time.sleep(d)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    _loads += 1
    print(f"  [LOAD {_loads}] {url[:80]}", flush=True)
    time.sleep(random.uniform(2, 3))
    if "checkpoint" in page.url or "challenge" in page.url:
        print("  [BLOCKED] LinkedIn challenge!", flush=True)
        return False
    return True


def scroll(page, n=3):
    for _ in range(n):
        page.mouse.wheel(0, random.randint(400, 700))
        time.sleep(random.uniform(0.4, 1))


def get_links(page):
    try:
        return page.evaluate("""() => {
            const a = document.querySelectorAll('a[href*="/in/"]');
            const u = [];
            a.forEach(el => {
                const h = (el.href||'').split('?')[0].replace(/\\/+$/, '');
                if (h.includes('/in/') && !u.includes(h)) u.push(h);
            });
            return u;
        }""") or []
    except:
        return []


def click_filter(page, label):
    try:
        r = page.evaluate("""(t) => {
            for (const b of document.querySelectorAll('button')) {
                const txt = (b.innerText||'').trim();
                if (txt.includes(t) && !txt.includes('toggle on')) { b.click(); return true; }
            }
            return false;
        }""", label)
        if r:
            time.sleep(random.uniform(2, 3))
        return r
    except:
        return False


def unclick_filter(page, label):
    try:
        page.evaluate("""(t) => {
            for (const b of document.querySelectorAll('button')) {
                const txt = (b.innerText||'').trim();
                if (txt.includes(t) && txt.includes('toggle on')) { b.click(); return; }
            }
        }""", label)
        time.sleep(random.uniform(1, 2))
    except:
        pass


def extract_filters(text):
    info = {"locations": {}, "roles": {}, "total": 0}
    lines = text.split("\n")
    section = None
    prev_line = ""
    for line in lines:
        line = line.strip()
        if not line:
            prev_line = ""
            continue
        if "associated member" in line.lower():
            for n in re.findall(r'(\d[\d,]*)', line):
                val = int(n.replace(",", ""))
                if val > info["total"]:
                    info["total"] = val
        if "Where they live" in line:
            section = "locations"; prev_line = line; continue
        elif "Where they studied" in line:
            section = None; prev_line = line; continue
        elif "What they do" in line:
            section = "roles"; prev_line = line; continue
        elif "What they are skilled at" in line or "People you may know" in line or line.startswith("Page "):
            section = None
        if section and line:
            if line in ("toggle off", "toggle on"):
                parts = prev_line.split(None, 1)
                if len(parts) == 2 and parts[0].replace(",", "").isdigit():
                    count = int(parts[0].replace(",", ""))
                    name = parts[1]
                    if section == "locations": info["locations"][name] = count
                    elif section == "roles": info["roles"][name] = count
            elif "toggle" in line:
                clean = line.replace("toggle off", "").replace("toggle on", "").strip()
                parts = clean.split(None, 1)
                if len(parts) == 2 and parts[0].replace(",", "").isdigit():
                    count = int(parts[0].replace(",", ""))
                    name = parts[1]
                    if section == "locations": info["locations"][name] = count
                    elif section == "roles": info["roles"][name] = count
        prev_line = line
    return info


def read_profile(page, url):
    """Visit profile, extract verified title from Experience section."""
    if not go(page, url, delay_range=DELAY_PROFILE):
        return None
    scroll(page, 2)

    try:
        main_el = page.query_selector("main")
        text = main_el.inner_text() if main_el else page.inner_text("body")
    except:
        return None

    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if not lines:
        return None

    skip = {"Open to", "Message", "More", "Connect", "Follow", "Pending",
            "Edit profile", "Add profile section", "Enhance profile", "Open"}

    name = ""
    headline = ""
    for ln in lines:
        if ln in skip or len(ln) < 2:
            continue
        if "followers" in ln.lower() and "connections" in ln.lower():
            continue
        if not name and ln[0].isalpha():
            name = ln
            continue
        if name and not headline:
            if ln not in skip and "followers" not in ln.lower() and "connections" not in ln.lower():
                headline = ln
                break

    # Parse Experience
    experiences = []
    in_exp = False
    entry = {}
    end_sections = {"Education", "Licenses & Certifications", "Skills",
                    "Recommendations", "Interests", "Activity", "Courses",
                    "Projects", "Volunteer Experience", "Publications",
                    "Honors & Awards", "Languages", "Organizations"}

    for ln in lines:
        if ln == "Experience":
            in_exp = True
            continue
        if in_exp and ln in end_sections:
            break
        if not in_exp:
            continue

        if " · " in ln and any(k in ln for k in ["yr", "mo", "Present"]):
            if entry.get("title"):
                entry["dates"] = ln
                experiences.append(entry)
                entry = {}
        elif " · " in ln and any(k in ln.lower() for k in
                ["full-time", "part-time", "contract", "intern", "freelance", "self-employed"]):
            if entry.get("title"):
                entry["type_line"] = ln
        elif not entry.get("title") and len(ln) > 2 and ln[0].isalpha() and ln not in skip:
            entry["title"] = ln
        elif entry.get("title") and not entry.get("org"):
            entry["org"] = ln

    if entry.get("title") and entry not in experiences:
        experiences.append(entry)

    cur_title = experiences[0]["title"] if experiences else headline
    cur_org = experiences[0].get("org", "").split(" · ")[0] if experiences else ""
    tenure = experiences[0].get("dates", "") if experiences else ""

    return {
        "name": name,
        "verified_title": cur_title,
        "org": cur_org,
        "tenure": tenure,
        "headline": headline,
        "linkedin": url,
    }


def collect_links_from_filter(page, role_label, visited):
    """Click a filter, collect new profile links, unclick."""
    if click_filter(page, role_label):
        scroll(page, 3)
        links = get_links(page)
        new = [l for l in links if l not in visited]
        unclick_filter(page, role_label)
        return new
    return []


def search_company(page, company_name, slug, city):
    """Filter → visit every profile from filtered results."""
    base_url = f"https://www.linkedin.com/company/{slug}/people/"

    print(f"\n{'='*60}", flush=True)
    print(f"  {company_name}  →  /{slug}/people/", flush=True)
    print(f"{'='*60}", flush=True)

    if not go(page, base_url):
        return []

    scroll(page, 2)
    text = page.query_selector("main").inner_text() if page.query_selector("main") else ""

    if "Page not found" in text or "page isn" in text.lower():
        print(f"  [SKIP] Not found", flush=True)
        return []

    filters = extract_filters(text)
    print(f"  Employees: {filters['total']}", flush=True)
    if filters["locations"]:
        print(f"  Locations: {filters['locations']}", flush=True)
    if filters["roles"]:
        print(f"  Roles: {filters['roles']}", flush=True)

    # City check
    city_aliases = {
        "delhi": ["delhi", "new delhi", "greater delhi", "ncr", "national capital"],
        "delhi ncr": ["delhi", "new delhi", "greater delhi", "gurugram", "gurgaon", "noida",
                      "faridabad", "ghaziabad", "ncr", "national capital"],
        "mumbai": ["mumbai", "greater mumbai", "navi mumbai", "thane"],
        "bangalore": ["bangalore", "bengaluru", "greater bengaluru"],
        "southeast asia": ["malaysia", "singapore", "indonesia", "thailand", "philippines",
                           "vietnam", "kuala lumpur", "jakarta", "bangkok", "manila",
                           "ho chi minh", "hanoi", "selangor", "johor", "penang"],
        "sea": ["malaysia", "singapore", "indonesia", "thailand", "philippines",
                "vietnam", "kuala lumpur", "jakarta", "bangkok", "manila",
                "ho chi minh", "hanoi", "selangor", "johor", "penang"],
    }
    aliases = city_aliases.get(city.lower(), [city.lower()])
    city_present = any(any(a in loc.lower() for a in aliases) for loc in filters["locations"])
    if not city_present and filters["locations"] and filters["total"] > 50:
        print(f"  [SKIP] No employees in {city}", flush=True)
        return []

    # Find matching city filter label
    city_filter_label = None
    for loc_name in filters["locations"]:
        if any(a in loc_name.lower() for a in aliases):
            city_filter_label = loc_name
            break

    if city_filter_label:
        print(f"\n  City filter: {city_filter_label}", flush=True)
    else:
        print(f"\n  No matching city filter — proceeding without", flush=True)

    visited_links = set()
    results = []

    # ── For each role: reload People page → click city → click role → collect → visit ──
    # Fresh page load per role ensures clean filter state
    role_targets = ["Sales", "Business Development", "Customer Success"]

    for role in role_targets:
        # Check if this role existed in initial filter scan
        match = [r for r in filters.get("roles", {}) if role.lower() in r.lower()]
        if not match:
            continue
        role_label = match[0]
        orig_count = filters["roles"].get(role_label, "?")

        print(f"\n  --- {role_label} ({orig_count}) + {city_filter_label or 'all locations'} ---", flush=True)

        # Reload People page for clean state
        if not go(page, base_url):
            break
        scroll(page, 2)

        # Click city filter first
        if city_filter_label:
            if not click_filter(page, city_filter_label):
                print(f"  WARNING: Could not click city filter", flush=True)
            else:
                scroll(page, 1)

        # Click role filter on top of city
        if not click_filter(page, role_label):
            print(f"  Could not click role filter '{role_label}'", flush=True)
            continue

        scroll(page, 3)
        links = get_links(page)
        new_links = [l for l in links if l not in visited_links]
        print(f"  {len(new_links)} new profile links", flush=True)

        for i, link in enumerate(new_links):
            visited_links.add(link)
            slug_part = link.split("/in/")[-1] if "/in/" in link else "?"
            print(f"  [{i+1}/{len(new_links)}] {slug_part}", flush=True)
            data = read_profile(page, link)
            if data and data["name"]:
                data["company"] = company_name
                data["filter_source"] = role_label
                results.append(data)

    # ── Keyword searches: navigate to ?keywords= → click city → collect → visit ──
    for kw in ["Founder", "CEO", "Director", "Head"]:
        kw_url = f"https://www.linkedin.com/company/{slug}/people/?keywords={kw}"
        print(f"\n  --- Keyword: {kw} + {city_filter_label or 'all locations'} ---", flush=True)
        if not go(page, kw_url):
            break
        scroll(page, 1)

        # Re-apply city filter after navigation
        if city_filter_label:
            if click_filter(page, city_filter_label):
                scroll(page, 1)
            else:
                print(f"  WARNING: Could not re-apply city filter", flush=True)

        links = get_links(page)
        new_links = [l for l in links if l not in visited_links]
        print(f"  {len(new_links)} new profile links", flush=True)

        for i, link in enumerate(new_links):
            visited_links.add(link)
            slug_part = link.split("/in/")[-1] if "/in/" in link else "?"
            print(f"  [{i+1}/{len(new_links)}] {slug_part}", flush=True)
            data = read_profile(page, link)
            if data and data["name"]:
                data["company"] = company_name
                data["filter_source"] = f"keyword:{kw}"
                results.append(data)

    # Deduplicate by name
    seen = set()
    unique = []
    for r in results:
        k = r["name"].lower().strip()
        if k not in seen:
            seen.add(k)
            unique.append(r)

    print(f"\n  {company_name}: {len(unique)} verified leads", flush=True)
    return unique


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--companies", required=True, help="Name:slug pairs, comma-separated")
    parser.add_argument("--city", default="Delhi NCR")
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    companies = []
    for entry in args.companies.split(","):
        entry = entry.strip()
        if ":" in entry:
            name, slug = entry.split(":", 1)
            companies.append((name.strip(), slug.strip()))
        else:
            print(f"ERROR: Format 'Name:slug'. Got: {entry}")
            sys.exit(1)

    for f in ["parent.lock", ".parentlock", "lock"]:
        p = Path(USER_DATA_DIR) / f
        if p.exists():
            try: p.unlink()
            except: pass

    fp_path = Path(FINGERPRINT_FILE)
    if fp_path.exists():
        print("Reusing saved fingerprint.", flush=True)
        with open(fp_path, "r", encoding="utf-8") as f:
            opts = json.load(f)
    else:
        print("Generating new fingerprint...", flush=True)
        Path(USER_DATA_DIR).mkdir(parents=True, exist_ok=True)
        launch_kwargs = {"os": CAMOUFOX_OS, "headless": False}
        if CAMOUFOX_EXE:
            launch_kwargs["executable_path"] = CAMOUFOX_EXE
        opts = cfx_launch_options(**launch_kwargs)
        opts["user_data_dir"] = USER_DATA_DIR
        with open(fp_path, "w", encoding="utf-8") as f:
            json.dump(opts, f, indent=2, ensure_ascii=False)

    try:
        with Camoufox(from_options=opts, persistent_context=True) as ctx:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)
            global _loads
            _loads = 1

            if "/login" in page.url or "/uas/" in page.url or "/checkpoint" in page.url:
                print("Not logged in. Please log in manually.", flush=True)
                page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded")
                for i in range(30):
                    time.sleep(10)
                    if "/feed" in page.url and "/login" not in page.url:
                        print("Login detected!", flush=True)
                        break
                    if i % 3 == 0:
                        print(f"  Waiting... ({(i+1)*10}s)", flush=True)
                else:
                    print("ERROR: Login timed out.", flush=True)
                    return
                time.sleep(3)

            print(f"Logged in. {len(companies)} companies, city={args.city}\n", flush=True)

            all_results = []
            for name, slug in companies:
                results = search_company(page, name, slug, args.city)
                all_results.extend(results)

            seen = set()
            final = []
            for r in all_results:
                k = r["name"].lower().strip()
                if k not in seen:
                    seen.add(k)
                    final.append(r)

            print(f"\n{'='*60}", flush=True)
            print(f"TOTAL: {len(final)} verified leads", flush=True)
            print(f"Page loads: {_loads}", flush=True)

            if args.output and final:
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(final, f, indent=2, ensure_ascii=False)
                print(f"Saved: {args.output}", flush=True)

    except Exception as e:
        import traceback
        print(f"Error: {e}", flush=True)
        traceback.print_exc()


if __name__ == "__main__":
    main()
