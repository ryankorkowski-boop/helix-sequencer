from __future__ import annotations

import argparse
from pathlib import Path

from helix_knowledge.official_docs_importer import import_official_docs
from helix_knowledge.search import search_cards
from helix_knowledge.sqlite_store import TechniqueCardStore
from helix_knowledge.user_notes_importer import import_user_notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Helix knowledge base helper.")
    sub = parser.add_subparsers(dest="command")
    import_notes = sub.add_parser("import-notes")
    import_notes.add_argument("file")
    import_notes.add_argument("--db", default="build/helix_knowledge.sqlite3")
    import_docs = sub.add_parser("import-official")
    import_docs.add_argument("file")
    import_docs.add_argument("--db", default="build/helix_knowledge.sqlite3")
    search = sub.add_parser("search")
    search.add_argument("query")
    search.add_argument("--db", default="build/helix_knowledge.sqlite3")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    store = TechniqueCardStore(Path(args.db))
    if args.command == "import-notes":
        cards = import_user_notes(Path(args.file))
        store.save_cards(cards)
        print(f"Imported {len(cards)} user-note cards.")
        return 0
    if args.command == "import-official":
        cards = import_official_docs(Path(args.file))
        store.save_cards(cards)
        print(f"Imported {len(cards)} official-doc cards.")
        return 0
    if args.command == "search":
        cards = search_cards(store.load_cards(), args.query)
        for card in cards:
            print(f"{card.id}: {card.title}")
        return 0
    return 1
