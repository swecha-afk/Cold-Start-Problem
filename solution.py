#!/usr/bin/env python3
"""Run the deterministic Cold Start extraction pipeline."""
import json
import sys
from pathlib import Path

from pipeline import (
    assemble_organisations_and_chats,
    assemble_people,
    classify_circles,
    extract_goals,
    extract_open_loops,
    load_input,
)


def main(input_dir, output_path):
    # Load data exactly as check.load_input does.
    chats, messages, seed = load_input(input_dir)

    person_ids = sorted({p for c in chats for p in c.get("participants", [])} - {"ME"})
    circle_info = classify_circles(messages, seed, chats)
    organisations, ties = assemble_organisations_and_chats(chats, messages, seed)
    people = assemble_people(person_ids, circle_info)

    out = {
        "people": people,
        "organisations": organisations,
        "chats": ties,
        "goals": extract_goals(messages, seed),
        "open_loops": extract_open_loops(chats, messages),
    }
    Path(output_path).write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
