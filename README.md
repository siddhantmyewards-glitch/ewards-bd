# eWards BD Plugin

Toolkit for the eWards BD/Partnerships team. Two skills for daily prospecting and demo preparation.

## Skills

### /lead-gen
Find companies and BD/Sales/CS contacts on LinkedIn for partnership outreach. Pushes leads to a Google Sheet (one tab per run) with combined company + people data.

**Requires:**
- Chrome browser with [Claude in Chrome](https://chromewebstore.google.com/detail/claude-in-chrome/) extension
- LinkedIn account logged in (use a secondary account)
- Python 3 + `openpyxl` (`pip install openpyxl`)

### /demo-prep
Prepare for an eWards product demo or sales call. Researches the prospect, maps their business to relevant eWards modules, generates a tailored demo flow and talking points cheat sheet.

**Requires:**
- Web search access

## Installation

1. Install the plugin in Claude Code or Claude Cowork
2. For `/lead-gen`: Install Chrome extension and `pip install openpyxl`
3. Both skills reference `company.md` (eWards product knowledge) — already bundled

## Environment Setup (for /lead-gen)

Create a `ldcred.env` file in your project root with LinkedIn credentials:

```
LINKEDIN_EMAIL=your-secondary-account@email.com
LINKEDIN_PASSWORD=your-password
```

**Never commit this file to git.**
