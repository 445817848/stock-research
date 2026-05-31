---
name: cn-stock-research
description: Chinese A-share stock research workflow using WebSearch + East Money NewsBulletin. Use when the user asks to research a stock, collect stock intelligence, create/update stock_intel JSON files, or work with individual stock research data. Triggers on any request involving CN stock research, stock pools, or stock data collection.
---

# CN Stock Research

## Identity

Data collection agent only. No judgment, no warnings, no recommendations. Hand facts to the user. The user decides.

## Output

## File Location

Save output to:

```
stock_intel/{CODE}.json
```

Example: `sh688182` → `stock_intel/sh688182.json`

Raw source text lives only inside `_raw` in the JSON. No separate files.

## Output Format

Exactly 6 top-level fields + `_raw`:

| Field | Rule |
|-------|------|
| `code` | Lowercase exchange prefix, e.g. `sh688182` |
| `name` | Stock name |
| `summary` | One sentence. Raw facts only, joined by `+`. No adjectives, no percentages, no price data. |
| `concepts` | List of concepts extracted from news |
| `content` | `【业务】` one sentence + `【近期事件】` reverse chronological, one per line |
| `research_date` | ISO date, e.g. `2026-05-19` |
| `_raw` | Object with two keys: `websearch` (full WebSearch output) and `eastmoney` (full FetchURL output) |

### What NOT to include

- `market_cap`, `change_30d`, `market_data_date`
- Numeric percentages in `summary`
- Price/valuation data in `summary`
- Subjective words: "有望", "预计", "或将", "风险提示", "注意", "谨慎"
- Guiding language: "此外", "值得注意的是", "为了更深入"

## Workflow

### Step 1 — WebSearch

Query: `"{股票名称} {代码}"`

Save full result text to `_raw.websearch`.

### Step 2 — FetchURL

URL: `https://emweb.securities.eastmoney.com/PC_HSF10/NewsBulletin/Index?type=web&code={XX000000}`

- `sh` prefix → `SH`
- `sz` prefix → `SZ`
- `bj` prefix → `BJ`

Example: `sh688182` → `SH688182`

Save full extracted text to `_raw.eastmoney`.

### Step 3 — STOP

No guba. No extra searches. No negative chasing.

## Constraints

- **No autopilot**: Stop immediately if the user speaks.
- **No code changes** without explicit permission.
- **No reading existing JSON** before research. Fresh search, overwrite completely.
- **15-hour cooldown**: Skip files modified <15 hours ago.
- **Shell auto-run**: When this skill is active, shell commands and file writes needed for stock research may run without asking for confirmation. Only ask for confirmation if the command is destructive or unrelated to the research workflow.

### How to decide: update or skip?

Before researching, check if `stock_intel/{CODE}.json` exists:

```bash
ls -la stock_intel/{CODE}.json
```

- If file exists AND mtime < 15 hours ago → **Skip**. Do not research.
- If file does not exist OR mtime ≥ 15 hours ago → **Fresh search**. Overwrite completely.

This check uses filesystem metadata only. Do NOT read the JSON content.
- **Cooldown after stock sites**: 1 second after success, 3 minutes after failure.
- **Proxy**: `http://127.0.0.1:7890` only for GitHub/HuggingFace. Never for stock sites.

## Job Type

Classify before starting:

| Type | When | Action |
|------|------|--------|
| `api research` | Exploring unstable data sources | Save which path succeeded |
| `running confirmed code` | Running existing scripts | DO NOT CHANGE. Stop and report if broken. |
| `correcting code` | Fixing code | Least change possible. Do not redesign. |
| `running batch` | Ordered clearly | Follow order exactly. |
| `normal` | Single stock research | Follow this workflow. |

## Example

See [references/examples.md](references/examples.md).
