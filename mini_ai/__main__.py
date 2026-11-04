"""Run with python -m mini_ai --help."""
import argparse
import json
from pathlib import Path
from .brief import summarize
from .search import PocketSearch
from .triage import InboxLens


def main():
    parser = argparse.ArgumentParser(description='Three explainable, offline NLP tools')
    commands = parser.add_subparsers(dest='command', required=True)
    search = commands.add_parser('search', help='Search a JSON array of text documents')
    search.add_argument('file', type=Path)
    search.add_argument('query')
    search.add_argument('--limit', type=int, default=3)
    triage = commands.add_parser('triage', help='Classify a message using labeled JSON examples')
    triage.add_argument('file', type=Path)
    triage.add_argument('text')
    triage.add_argument('--threshold', type=float, default=0.65)
    brief = commands.add_parser('brief', help='Extract sentences from a UTF-8 text file')
    brief.add_argument('file', type=Path)
    brief.add_argument('--sentences', type=int, default=3)
    args = parser.parse_args()
    try:
        raw = args.file.read_text(encoding='utf-8')
        if args.command == 'brief':
            result = summarize(raw, args.sentences)
        else:
            data = json.loads(raw)
            if not isinstance(data, list):
                raise ValueError('JSON input must be an array')
            if args.command == 'search':
                if not all(isinstance(item, str) for item in data):
                    raise ValueError('Search documents must be strings')
                result = PocketSearch(data).search(args.query, args.limit)
            else:
                result = InboxLens(data).predict(args.text, args.threshold)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except (OSError, UnicodeError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == '__main__':
    main()
