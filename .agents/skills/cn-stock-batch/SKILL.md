---
name: cn-stock-batch
description: Batch orchestration for Chinese A-share stock research. Use when the user provides a list of multiple stocks to research, update, or collect in one session. Triggers on requests like "research these stocks", "do a batch", "update this list", or any multi-stock research request. Works alongside cn-stock-research skill.
---

# CN Stock Batch Research

## Purpose

Take a list of stocks, shrink it using the 15-hour cooldown rule, then process survivors **one at a time** using the `cn-stock-research` workflow.

## Input Format

The user provides a list. Accept any format:

- Code only: `600519 002594 300308 601127 000858`
- Code + name: `600519 贵州茅台, 002594 比亚迪`
- JSON array: `[{"code":"sh600519","name":"贵州茅台"}, ...]`

## Step 1 — Shrink the List

Run a shell check against `stock_intel/` to filter out stocks modified < 15 hours ago.

Example command for a small list:

```bash
for code in 600519 002594 300308 601127 000858; do
    file="stock_intel/${code}.json"
    if [ -f "$file" ]; then
        age_hours=$(( ($(date +%s) - $(stat -c %Y "$file")) / 3600 ))
        if [ "$age_hours" -lt 15 ]; then
            echo "SKIP $code: ${age_hours}h old"
        else
            echo "NEED $code: ${age_hours}h old"
        fi
    else
        echo "NEED $code: missing"
    fi
done
```

Report the filtered list to the user before proceeding.

## Step 2 — Sequential Processing

For each stock in the filtered list, run the `cn-stock-research` skill **in full** before moving to the next.

Do NOT substitute your own shorthand. Do NOT skip steps. Follow that skill's rules exactly — including WebSearch query format, East Money URL construction, output format, and the `_raw` requirement to save complete unedited tool output.

After the skill finishes one stock, save the result to `stock_intel/{CODE}.json`, log progress, then proceed to the next stock.

## Hard Rules

- **NEVER concurrent IO**: One stock at a time. No parallel WebSearch. No parallel FetchURL. No background tasks.
- **NEVER batch the tools**: Each stock gets its own discrete WebSearch + FetchURL cycle.
- **ALWAYS cooldown**: 1 second after successful stock site read, 3 minutes after failure.
- **ALWAYS stop if user speaks**: Address the user immediately. Do not finish the current stock.
- **NEVER read existing JSON content**: Fresh search only. Overwrite completely.

## Progress Tracking

After each stock, report:

```
[1/5] 600519 贵州茅台 — DONE
[2/5] 002594 比亚迪 — SKIPPED (too fresh)
[3/5] 300308 中际旭创 — DONE
```

## Job Type

This is `running batch`. Follow the order exactly. No additions, no skips beyond the 15h filter.
