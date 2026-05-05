#!/usr/bin/env python3
"""
LinkedIn API Scraper for eWards Lead Generation
Uses linkedin-api (tomquirk) to search for companies and people.
Rate-limited to avoid account restrictions.

Usage:
    python linkedin_scraper.py --type "POS vendor" --city "Chennai" --limit 50 --env-file .env
"""

import argparse
import json
import os
import sys
import time
import random
from datetime import datetime
from pathlib import Path


def load_env(env_path):
    """Load credentials from .env file."""
    creds = {}
    env_file = Path(env_path)
    if not env_file.exists():
        print(f"ERROR: {env_path} not found.")
        print("Create a .env file with:")
        print("  LINKEDIN_EMAIL=your@email.com")
        print("  LINKEDIN_PASSWORD=yourpassword")
        sys.exit(1)

    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                creds[key.strip()] = value.strip()

    if 'LINKEDIN_EMAIL' not in creds or 'LINKEDIN_PASSWORD' not in creds:
        print("ERROR: .env must contain LINKEDIN_EMAIL and LINKEDIN_PASSWORD")
        sys.exit(1)

    return creds


def safe_delay(min_sec=2, max_sec=4):
    """Random delay between requests to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def authenticate(email, password):
    """Authenticate with LinkedIn. Returns API object or exits."""
    try:
        from linkedin_api import Linkedin
    except ImportError:
        print("ERROR: linkedin-api not installed.")
        print("Run: pip install linkedin-api")
        sys.exit(1)

    print(f"Authenticating as {email}...")
    try:
        api = Linkedin(email, password)
        print("Authentication successful.")
        return api
    except Exception as e:
        error_msg = str(e).lower()
        if 'challenge' in error_msg or 'captcha' in error_msg or 'verification' in error_msg:
            print("\n" + "="*60)
            print("CAPTCHA / VERIFICATION REQUIRED")
            print("="*60)
            print("LinkedIn is asking for human verification.")
            print("1. Open LinkedIn in your browser")
            print("2. Log in with this secondary account")
            print("3. Solve any CAPTCHA or security challenge")
            print("4. Once done, run this script again")
            print("="*60)
            sys.exit(2)
        else:
            print(f"ERROR: Authentication failed: {e}")
            sys.exit(1)


def search_companies(api, keywords, city, limit=20):
    """Search for companies matching keywords + location."""
    companies = []
    search_queries = [
        f"{keywords} {city}",
        f"{keywords} in {city}",
    ]

    for query in search_queries:
        if len(companies) >= limit:
            break

        print(f"  Searching companies: '{query}'...")
        try:
            results = api.search_companies(keywords=query, limit=min(limit, 10))
            safe_delay()
        except Exception as e:
            print(f"  Warning: Company search failed for '{query}': {e}")
            safe_delay(4, 6)
            continue

        if not results:
            continue

        for result in results:
            if len(companies) >= limit:
                break

            company = {
                "name": "",
                "website": "",
                "linkedin_url": "",
                "urn_id": "",
                "source": "linkedin_api"
            }

            # Extract company data from search result
            if isinstance(result, dict):
                company["name"] = result.get("name", "")
                urn = result.get("urn_id", "") or result.get("entityUrn", "") or result.get("urn", "")
                if urn:
                    company["urn_id"] = urn
                    # Build LinkedIn URL from universal name or URN
                    universal_name = result.get("universalName", "")
                    if universal_name:
                        company["linkedin_url"] = f"https://www.linkedin.com/company/{universal_name}/"
                    elif "company:" in str(urn):
                        company_id = str(urn).split("company:")[-1].split(",")[0].split(")")[0]
                        company["linkedin_url"] = f"https://www.linkedin.com/company/{company_id}/"

            if company["name"]:
                # Check for duplicates
                if not any(c["name"].lower() == company["name"].lower() for c in companies):
                    companies.append(company)
                    print(f"    Found: {company['name']}")

        safe_delay()

    # Try to get website URLs for companies with URN IDs
    for company in companies:
        if company["urn_id"] and not company["website"]:
            try:
                universal_name = company["linkedin_url"].split("/company/")[-1].rstrip("/") if company["linkedin_url"] else ""
                if universal_name:
                    details = api.get_company(universal_name)
                    safe_delay(2, 3)
                    if details:
                        website = details.get("companyPageUrl", "") or details.get("website", "")
                        if not website:
                            # Try nested structure
                            website = (details.get("callToAction", {}) or {}).get("url", "")
                        if not website:
                            websites = details.get("confirmedLocations", [])
                            # Sometimes website is in different fields
                            for key in ["websiteUrl", "companyPageUrl", "url"]:
                                if key in details:
                                    website = details[key]
                                    break
                        company["website"] = website or ""
            except Exception as e:
                print(f"    Warning: Could not fetch details for {company['name']}: {e}")
                safe_delay(3, 5)

    return companies


def search_people(api, keywords, city, companies, limit=30):
    """Search for people at discovered companies + general keyword search."""
    people = []
    request_count = 0
    max_requests = 80  # daily safety limit

    # Strategy 1: Search by keywords + city
    title_groups = [
        '"founder" OR "CEO" OR "co-founder" OR "managing director"',
        '"sales" OR "business development" OR "head of sales"',
        '"director" OR "VP" OR "general manager"'
    ]

    for titles in title_groups:
        if len(people) >= limit or request_count >= max_requests:
            break

        query = f"{keywords} {city}"
        print(f"  Searching people: '{query}'...")
        try:
            results = api.search_people(
                keywords=query,
                limit=min(limit, 10)
            )
            request_count += 1
            safe_delay()
        except Exception as e:
            print(f"  Warning: People search failed: {e}")
            safe_delay(4, 6)
            continue

        if not results:
            continue

        for result in results:
            if len(people) >= limit:
                break

            person = extract_person(result)
            if person and person["name"]:
                if not any(p["name"].lower() == person["name"].lower() and
                          p["company"].lower() == person["company"].lower() for p in people):
                    people.append(person)
                    print(f"    Found: {person['name']} — {person['designation']} at {person['company']}")

    # Strategy 2: Search within specific companies found earlier
    for company in companies:
        if len(people) >= limit or request_count >= max_requests:
            break

        if not company["name"]:
            continue

        print(f"  Searching people at {company['name']}...")
        try:
            results = api.search_people(
                keywords=company["name"],
                limit=5
            )
            request_count += 1
            safe_delay()
        except Exception as e:
            print(f"  Warning: Search failed for {company['name']}: {e}")
            safe_delay(4, 6)
            continue

        if not results:
            continue

        for result in results:
            if len(people) >= limit:
                break

            person = extract_person(result)
            if person and person["name"]:
                # Override company name with the one we searched for if it matches
                if not person["company"]:
                    person["company"] = company["name"]

                if not any(p["name"].lower() == person["name"].lower() and
                          p["company"].lower() == person["company"].lower() for p in people):
                    people.append(person)
                    print(f"    Found: {person['name']} — {person['designation']} at {person['company']}")

    print(f"\n  Total API requests made: {request_count}")
    return people


def extract_person(result):
    """Extract person data from a LinkedIn search result."""
    person = {
        "name": "",
        "designation": "",
        "company": "",
        "linkedin_url": "",
        "source": "linkedin_api"
    }

    if not isinstance(result, dict):
        return None

    # Name
    first = result.get("firstName", "") or result.get("first_name", "") or ""
    last = result.get("lastName", "") or result.get("last_name", "") or ""
    person["name"] = f"{first} {last}".strip()

    # Designation / Headline
    person["designation"] = result.get("headline", "") or result.get("title", "") or result.get("occupation", "") or ""

    # Company — try multiple fields
    person["company"] = result.get("companyName", "") or result.get("company", "") or ""
    if not person["company"]:
        # Sometimes nested in different structures
        summary = result.get("summary", "") or result.get("headline", "") or ""
        if " at " in summary:
            person["company"] = summary.split(" at ")[-1].strip()
        elif " @ " in summary:
            person["company"] = summary.split(" @ ")[-1].strip()

    # LinkedIn URL
    public_id = result.get("public_id", "") or result.get("publicIdentifier", "") or result.get("urn_id", "")
    if public_id:
        # public_id is the URL slug
        if not public_id.startswith("http"):
            person["linkedin_url"] = f"https://www.linkedin.com/in/{public_id}/"
        else:
            person["linkedin_url"] = public_id

    return person


def main():
    parser = argparse.ArgumentParser(description="LinkedIn API Lead Scraper")
    parser.add_argument("--type", required=True, help="Company type (e.g., 'POS vendor')")
    parser.add_argument("--city", required=True, help="City (e.g., 'Chennai')")
    parser.add_argument("--limit", type=int, default=30, help="Max leads to find (default: 30)")
    parser.add_argument("--env-file", default=".env", help="Path to .env file")
    parser.add_argument("--output", default=None, help="Output JSON file path")
    args = parser.parse_args()

    if not args.output:
        safe_type = args.type.replace(" ", "_").lower()
        safe_city = args.city.replace(" ", "_").lower()
        date_str = datetime.now().strftime("%Y%m%d")
        args.output = f"linkedin_raw_{safe_type}_{safe_city}_{date_str}.json"

    print("="*60)
    print(f"eWards Lead Gen — LinkedIn API Scraper")
    print(f"Type: {args.type}")
    print(f"City: {args.city}")
    print(f"Target: {args.limit} leads")
    print("="*60)

    # Load credentials
    creds = load_env(args.env_file)

    # Authenticate
    api = authenticate(creds["LINKEDIN_EMAIL"], creds["LINKEDIN_PASSWORD"])

    # Search companies
    print(f"\n--- Searching Companies ---")
    company_limit = max(args.limit // 3, 10)
    companies = search_companies(api, args.type, args.city, limit=company_limit)
    print(f"Found {len(companies)} companies.\n")

    # Search people
    print(f"--- Searching People ---")
    people = search_people(api, args.type, args.city, companies, limit=args.limit)
    print(f"Found {len(people)} people.\n")

    # Save output
    output = {
        "metadata": {
            "type": args.type,
            "city": args.city,
            "date": datetime.now().isoformat(),
            "source": "linkedin_api"
        },
        "companies": companies,
        "people": people
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Results saved to: {args.output}")
    print(f"  Companies: {len(companies)}")
    print(f"  People: {len(people)}")

    return args.output


if __name__ == "__main__":
    main()
