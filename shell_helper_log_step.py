import sys
import json
import time
import os

def main():
    if len(sys.argv) < 4:
        print("Usage: python shell_helper_log_step.py <batch_id> <stock_code> <step> [status] [extra_json]", file=sys.stderr)
        sys.exit(1)

    batch_id = sys.argv[1]
    stock_code = sys.argv[2]
    step = sys.argv[3]
    status = sys.argv[4] if len(sys.argv) > 4 else None
    extra = {}
    if len(sys.argv) > 5:
        try:
            extra = json.loads(sys.argv[5])
        except json.JSONDecodeError:
            extra = {"raw": sys.argv[5]}

    log_dir = "batch_logs"
    os.makedirs(log_dir, exist_ok=True)

    record = {
        "ts": int(time.time()),
        "stock": stock_code,
        "step": step,
    }
    if status:
        record["status"] = status
    if extra:
        record.update(extra)

    log_path = os.path.join(log_dir, f"batch_{batch_id}.jsonl")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"Logged: {record}")

if __name__ == "__main__":
    main()
