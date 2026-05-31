"""CLI entry point for cnstock-gap."""

import argparse
import sys

from .core import ratelimit
from .sources import sina, tencent, eastmoney


def _bars_per_day(scale: int) -> int:
    """A-share trading day = 4 hours = 240 minutes."""
    if scale == 240:
        return 1
    return 240 // scale


# Conservative day limits per scale to avoid API blocking
_MAX_DAYS = {
    5: 5,    # 5min: dense data, keep conservative
    30: 20,  # 30min: ~160 bars
    60: 30,  # 60min: ~120 bars
    240: 90, # daily: ~90 bars, single request
}


def cmd_kline(args):
    """Handle `csg kline`."""
    ratelimit.reset_budget()

    max_days = _MAX_DAYS.get(args.scale, 5)
    if args.days > max_days:
        print(
            f"[error] scale={args.scale} max days={max_days}. "
            f"Requested {args.days} days exceeds safe limit. Aborting.",
            file=sys.stderr,
        )
        sys.exit(1)

    datalen = args.days * _bars_per_day(args.scale) + 5  # +5 for MA5 buffer
    data = sina.fetch_kline(args.code, scale=args.scale, datalen=datalen)

    for bar in data:
        print(
            f"day={bar['day']} open={bar['open']} high={bar['high']} "
            f"low={bar['low']} close={bar['close']} volume={bar['volume']}"
        )

    print(f"[requests spent: {ratelimit.get_total_requests()} | budget: unlimited]")


def cmd_snapshot(args):
    """Handle `csg snapshot`."""
    ratelimit.reset_budget()

    codes = [c.strip() for c in args.codes.split(",") if c.strip()]
    data = tencent.fetch_snapshot(codes)

    for s in data:
        print(
            f"code={s['code']} name={s['name']} price={s['price']} "
            f"open={s['open']} high={s['high']} low={s['low']} "
            f"prev={s['prev_close']} change_pct={s['change_pct']}% "
            f"volume={s['volume']} turnover={s['turnover']}"
        )

    print(f"[requests spent: {ratelimit.get_total_requests()} | budget: unlimited]")


def cmd_ranking(args):
    """Handle `csg ranking`."""
    ratelimit.reset_budget()

    data = eastmoney.fetch_ranking(
        rank_type="gainers",
        pages=args.pages,
        min_change=args.min_change,
    )

    for s in data[: args.top]:
        print(
            f"code={s['code']} name={s['name']} price={s['price']} "
            f"change_pct={s['change_pct']}% change_amt={s['change_amt']} "
            f"open={s['open']} prev={s['prev_close']} "
            f"volume={s['volume']} turnover={s['turnover']} cap={s['market_cap']}"
        )

    print(f"[requests spent: {ratelimit.get_total_requests()} | budget: unlimited]")


def main():
    parser = argparse.ArgumentParser(
        prog="csg",
        description="cnstock-gap: A-share data gap-filler CLI",
    )
    subparsers = parser.add_subparsers(dest="command")

    # kline subcommand
    kline_p = subparsers.add_parser("kline", help="Fetch K-line bars")
    kline_p.add_argument("code", help="Stock code, e.g. 301666")
    kline_p.add_argument(
        "--scale",
        type=int,
        default=240,
        choices=[5, 30, 60, 240],
        help="Bar interval in minutes (default: 240 = daily). "
             "Max days: 5min→5, 30min→10, 60min→15, daily→20",
    )
    kline_p.add_argument(
        "--days",
        type=int,
        default=45,
        help="Number of trading days (default: 45). Max: 5min→5, 30min→20, 60min→30, daily→90",
    )

    # snapshot subcommand
    snap_p = subparsers.add_parser("snapshot", help="Fetch batch real-time snapshots")
    snap_p.add_argument(
        "codes",
        help="Comma-separated stock codes, e.g. 301666,600519,000001",
    )

    # ranking subcommand
    rank_p = subparsers.add_parser("ranking", help="Fetch top gainers ranking")
    rank_p.add_argument(
        "--pages", type=int, default=2, help="Number of pages to fetch (default: 2)"
    )
    rank_p.add_argument(
        "--min-change", type=float, default=None, help="Minimum change_pct filter"
    )
    rank_p.add_argument(
        "--top", type=int, default=20, help="Number of results to print (default: 20)"
    )

    args = parser.parse_args()
    if args.command == "kline":
        cmd_kline(args)
    elif args.command == "snapshot":
        cmd_snapshot(args)
    elif args.command == "ranking":
        cmd_ranking(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
