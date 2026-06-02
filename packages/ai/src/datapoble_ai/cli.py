"""Tiny CLI for manual smoke checks (no UI; that's Mirador's job).

    python -m datapoble_ai.cli "Quin municipi té més IETR?" --locale ca
    python -m datapoble_ai.cli "¿Cuántas viviendas no principales tiene Castellar de n'Hug?" --locale es --json
"""

from __future__ import annotations

import argparse
import json
import sys

from .agent import Agent


def _force_utf8_stdout() -> None:
    """Ensure accented ca/es output prints on legacy Windows code pages."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    _force_utf8_stdout()
    parser = argparse.ArgumentParser(prog="datapoble_ai", description=__doc__)
    parser.add_argument("question", help="Natural-language question")
    parser.add_argument("--locale", default=None, help="ca | es (default: contract default)")
    parser.add_argument("--mode", default="auto", choices=["auto", "offline", "openrouter"])
    parser.add_argument("--json", action="store_true", help="Emit the full structured answer")
    args = parser.parse_args(argv)

    with Agent(mode=args.mode) as agent:
        ans = agent.ask(args.question, locale=args.locale)
        if args.json:
            print(json.dumps(ans.to_dict(), ensure_ascii=False, indent=2))
        else:
            tag = "REFUSAL" if ans.is_refusal else "OK"
            print(f"[{ans.backend}] {tag}")
            print(ans.text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
