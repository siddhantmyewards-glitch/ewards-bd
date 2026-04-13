---
name: demo-prep
description: Prepare for an eWards product demo or sales call with a prospect. Use when asked to prep for a demo, prepare for a call, research a prospect before a meeting, build a demo flow, create talking points for a pitch, or plan a presentation for a brand. Triggered by company name — researches the prospect and generates a tailored eWards demo strategy.
---

# eWards Demo Prep Skill

Prepare a tailored demo flow and talking points for an eWards sales call. Research the prospect, map their business to eWards features, and deliver a ready-to-use demo plan.

## Execution Flow

### Step 1: Get the Prospect

Ask the user (via AskUserQuestion) for:

**1. Company name?** (free text)

**2. What do you know about them?**
Options: Nothing, just the name | I have some context | They're an existing lead from /lead-gen

**3. What's the meeting type?**
Options: First intro / discovery call | Product demo | Follow-up / negotiation | Partnership pitch

Wait for answers before proceeding.

### Step 2: Research the Prospect

Use web search to gather:
- **Company basics** — what they do, industry vertical, founding year, HQ city
- **Size & scale** — number of outlets/stores, employee count, revenue indicators
- **Current tech stack** — what POS, CRM, loyalty, or marketing tools they use (if discoverable)
- **Recent news** — funding, expansion, new launches, partnerships
- **Customer base** — who their end customers are (retail shoppers, diners, etc.)

Run 3-5 searches:
- `"{company name}" about`
- `"{company name}" stores OR outlets OR locations India`
- `"{company name}" POS OR CRM OR loyalty OR rewards`
- `"{company name}" news 2025 OR 2026`

Summarize findings in a clean **Prospect Snapshot** section.

### Step 3: Map to eWards Products

Read `references/company.md` for the full eWards product suite and case studies.

Based on the prospect's industry and needs, map relevant eWards modules:

| Prospect Signal | eWards Module to Pitch |
|---|---|
| Retail / F&B with walk-in customers | nGine (Loyalty & Rewards) |
| Multiple outlets | nAlytics (Multi-outlet comparison, heat maps) |
| Running SMS/WhatsApp campaigns | nGage (Omnichannel Campaign Engine) |
| No digital receipts | nVoice (Digital Invoice) |
| Wants customer feedback | Loop (Feedback Module) |
| Needs data-driven marketing | InsightX (AI-Powered CRM Intelligence) |
| Wants online store | Ping (eCommerce App/Website) |
| Already has a POS | Highlight relevant POS integration from the 30+ partners |
| Using a competitor CRM/loyalty | Position eWards differentiators |

Only pitch modules that are relevant. Do NOT dump the entire product suite — tailor it.

### Step 4: Generate Demo Flow

Create a structured demo plan:

**1. Opening (2 min)**
- Personalized hook referencing their business
- Agenda overview

**2. Discovery Questions (5 min)**
- Generate 3-5 questions specific to their industry to understand pain points
- E.g., "How do you currently track repeat customers across your X outlets?"

**3. Product Walkthrough (15 min)**
- Order the eWards modules by relevance to THIS prospect
- For each module: one-line what it does + how it solves THEIR specific problem
- Reference a matching case study from `references/company.md` where possible

**4. Differentiators (3 min)**
- Pick 3-4 differentiators most relevant to this prospect (from the 12 listed in company.md)
- Frame each as a comparison to what they're likely using now

**5. Next Steps (2 min)**
- Suggest a concrete next step based on meeting type

### Step 5: Generate Talking Points

Create a bullet-point cheat sheet:

- **Ice breakers** — 2-3 personalized conversation starters based on their recent news/growth
- **Pain point angles** — 3-4 pain points common in their industry that eWards solves
- **Case study drops** — which case studies to reference and when (from company.md)
- **Objection handling** — 3-4 common objections and responses:
  - "We already have a loyalty program" -> integration/migration angle
  - "We're too small" -> no per-user fees, fast onboarding
  - "We need to think about it" -> offer pilot/trial
  - "What about data security?" -> cloud-based, 99.9% uptime SLA
- **Competitor angles** — if they use a known competitor, key differentiators to highlight

### Step 6: Output

Present everything in a clean, scannable format:

```
## Prospect Snapshot
[company basics, size, tech stack, recent news]

## Recommended Demo Flow
[ordered module walkthrough with timing]

## Talking Points Cheat Sheet
[ice breakers, pain points, case studies, objections]
```

Keep it concise — this is a prep doc to skim 10 minutes before a call, not a 20-page report.

Do NOT fabricate company details. If something is unknown, say so and suggest the user verify it.
