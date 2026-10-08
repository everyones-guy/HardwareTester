"""Start one lab owner process; bind locally unless explicitly configured otherwise."""

import argparse
from Hardware_Tester_App import create_app


def main():
    parser = argparse.ArgumentParser(
        description="Hardware Tester Flask workbench backend"
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app = create_app()
    from waitress import serve

    try:
        print(f"Hardware Tester backend: http://{args.host}:{args.port}", flush=True)
        serve(app, host=args.host, port=args.port, threads=4)
    finally:
        # atexit owns shutdown; avoids double-closing the SQLite connection.
        pass


if __name__ == "__main__":
    main()
