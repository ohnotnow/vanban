# vanban

Monitor Vanilla Forum comments for policy violations via OpenAI Moderation.

## Table of Contents  
1. [Description](#description)  
2. [Features](#features)  
3. [Prerequisites](#prerequisites)  
4. [Installation](#installation)  
5. [Configuration](#configuration)  
6. [Usage](#usage)  
7. [Environment Variables](#environment-variables)  
8. [Example](#example)  
9. [License](#license)  

## Description  
`vanban` fetches recent comments from a Vanilla Forum instance, submits them to the OpenAI Moderation API, and emits a Markdown report of any flagged content.  

## Features  
- Fetch unlimited pages of comments (with optional time window)  
- Configurable moderation threshold, lookback period, page size  
- Safe extraction of commenter display names  
- Rate-limit-friendly delays between API calls  
- Markdown-formatted output  

## Prerequisites  
- Git  
- Python 3.8+  
- [uv](https://docs.astral.sh/uv/) (for dependency management and script execution)  
- A valid OpenAI API key  
- A Vanilla Forum API token  

## Installation  

```bash
# 1. Clone the repository
git clone https://github.com/ohnotnow/vanban.git
cd vanban

# 2. Install dependencies via uv
uv sync
```

> Note: If you do not have `uv` installed, follow the instructions at https://docs.astral.sh/uv/.  

## Configuration  
Create a `.env` file in the project root or export variables in your shell. Required variables:

- `OPENAI_API_KEY` – Your OpenAI API key  
- `VANILLA_API_TOKEN` – Your Vanilla Forum API token  

Optional variables (defaults shown):

- `VANILLA_BASE_URL` – Forum URL (default: `https://forum.example.com`)  
- `MODERATION_THRESHOLD` – Minimum category score to flag (default: `0.01`)  
- `LOOKBACK_HOURS` – Hours back to scan (0 = no cutoff; default: `24`)  
- `PAGE_SIZE` – Comments per API page (default: `100`)  

### macOS / Linux  
```bash
export OPENAI_API_KEY="sk-..."
export VANILLA_API_TOKEN="token-..."
# optional overrides
export VANILLA_BASE_URL="https://forum.mycompany.com"
export MODERATION_THRESHOLD=0.05
export LOOKBACK_HOURS=12
export PAGE_SIZE=200
```

### Windows (PowerShell)  
```powershell
$env:OPENAI_API_KEY   = "sk-..."
$env:VANILLA_API_TOKEN= "token-..."
# optional overrides
$env:VANILLA_BASE_URL    = "https://forum.mycompany.com"
$env:MODERATION_THRESHOLD= "0.05"
$env:LOOKBACK_HOURS      = "12"
$env:PAGE_SIZE           = "200"
```

## Usage  

```bash
uv run main.py
```

This command will:  
1. Fetch recent comments from your Vanilla Forum.  
2. Submit comment bodies to the OpenAI Moderation endpoint.  
3. Print a Markdown table of flagged posts to stdout.  

### Redirecting Output  
Save the report to a file:

```bash
uv run main.py > moderation_report.md
```

## Example Output  

```markdown
| User        | Comment                                         | Reason                    |
|-------------|-------------------------------------------------|---------------------------|
| user_123    | [link](https://forum.example.com/discussion/…)  | hate (0.12), threat (0.03)|
| alice       | [link](https://forum.example.com/discussion/…)  | sexual (0.02)             |
```

If no posts are flagged, the script prints:

```text
_No policy concerns detected in the selected window._
```

## License  
This project is licensed under the MIT License.
