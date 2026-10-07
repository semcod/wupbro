"""CLI entry-point: `python -m wupbro` or `wupbro`."""

from __future__ import annotations

import argparse
import os


def main() -> None:
    try:
        from .autoupdate import check_for_updates
        check_for_updates("wupbro")
    except Exception:
        try:
            from wupbro.autoupdate import check_for_updates
            check_for_updates("wupbro")
        except Exception:
            pass
    parser = argparse.ArgumentParser(prog="wupbro", description="WUP Browser Dashboard")
    parser.add_argument("--host", default=os.environ.get("WUPBRO_HOST", "0.0.0.0"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("WUPBRO_PORT", "8000")))
    parser.add_argument("--reload", action="store_true", help="auto-reload (dev)")
    args = parser.parse_args()

    import uvicorn
    uvicorn.run("wupbro.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()
