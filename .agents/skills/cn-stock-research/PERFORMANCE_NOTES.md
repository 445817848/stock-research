# Batch Performance Notes

## Background

Timing analysis from batch run `batch_1779346826` (9 stocks completed, subagent with per-step logging).

## Per-Step Timing (averages across 9 stocks)

| Step | Avg Duration | Notes |
|------|-------------|-------|
| WebSearch | **11.1s** | Network call, reasonable |
| FetchURL (East Money) | **13.9s** | Network call, reasonable |
| `fetchurl_end → save_json` | **31.4s** | ⭐ JSON composition + WriteFile |
| `save_json → cooldown` | **4.7s** | WriteFile wrap-up + cooldown start |
| `cooldown → progress_updated` | **14.7s** | ⭐ Read/modify/write `batch_progress.json` |
| Gap between tools | **4.1s** | Inter-tool overhead |

## Key Findings

### 1. File I/O is the bottleneck, not network

- **Writing a single `stock_intel/{code}.json` (~3KB) takes 31.4s on average.**
  - Worst case: `sh600584` took **54s**.
  - This is not disk speed — it is subagent WriteFile tool overhead or JSON composition latency.

- **Updating `batch_progress.json` (~40KB) takes 14.7s on average.**
  - Reading + modifying + writing a small JSON should be near-instant.
  - Subagent file operations are significantly slower than root-agent file operations.

### 2. Network calls are fine

| Call | Avg | Status |
|------|-----|--------|
| WebSearch | 11.1s | ✅ Acceptable |
| FetchURL | 13.9s | ✅ Acceptable |

### 3. Foreground vs background comparison

| Mode | Per-stock avg | Key difference |
|------|--------------|----------------|
| Root agent (foreground) | **74s** | File I/O is fast |
| Subagent (background, no retry) | **90s** | File I/O is slower |
| Subagent (background, standard) | **241s** | Hit retry cooldowns |

## Recommendations

1. **For speed**: Run batches in the **root agent** if possible. Subagent file I/O adds ~15–20s per stock.
2. **For unattended runs**: Use subagent with **no-retry on network errors** to avoid 3-minute cooldown stalls.
3. **For logging**: Log only `stock_start` and `stock_end` (2 entries per stock) instead of every sub-step. Full per-step logging doubles tool-call count and can hit the 100-step agent limit.
4. **Batch size**: Keep subagent batches to **≤5 stocks** if using full per-step logging, or **≤8 stocks** with minimal logging.

## Raw Data

Log file: `batch_logs/batch_1779346826.jsonl`
