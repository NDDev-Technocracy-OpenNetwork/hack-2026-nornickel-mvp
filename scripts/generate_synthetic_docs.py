from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sample_docs" / "synthetic" / "generated"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "README.txt").write_text(
        (
            "Generated binary fixtures are intentionally deferred until fixture dependencies "
            "are installed.\n"
            "The committed CSV/Markdown fixtures are the authoritative smoke-test fixtures "
            "for scaffold P0.\n"
        ),
        encoding="utf-8",
    )
    print(f"Generated fixture manifest at {OUT / 'README.txt'}")


if __name__ == "__main__":
    main()
