#!/usr/bin/env python3
"""
Insert a new bank entry into src/eul/banks.py BANKS dict.
Called by add-bank.sh — not intended for direct use.

Usage:
  python3 scripts/_register_bank.py <name> <strain> <path> <samples>
    [--slices N] [--weight N] [--no-loop]
"""
import sys
import argparse

BANKS_FILE = "src/eul/banks.py"

STRAIN_SECTIONS = {
    "Drone":   "# Drone (d1)",
    "Texture": "# Texture (d2)",
    "Chord":   "# Chords (d6)",
    "Voice":   "# Voice (d5)",
    "Drum":    "# Drums (d4)",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("name")
    p.add_argument("strain", choices=STRAIN_SECTIONS)
    p.add_argument("path")
    p.add_argument("samples", type=int)
    p.add_argument("--slices", type=int)
    p.add_argument("--weight", type=int)
    p.add_argument("--no-loop", action="store_true")
    args = p.parse_args()

    with open(BANKS_FILE) as f:
        lines = f.readlines()

    if any(f'"{args.name}":' in line for line in lines):
        sys.exit(f"Error: bank '{args.name}' already exists in {BANKS_FILE}")

    entry = f'"{args.name}": {args.strain}("{args.path}", samples={list(range(args.samples))}'
    if args.weight is not None:
        entry += f", weight={args.weight}"
    if args.slices is not None:
        entry += f", slices={args.slices}"
    if args.no_loop:
        entry += ", looping=False"
    entry = f"    {entry}),\n"

    # Insert at the end of the strain's section: find its header comment,
    # then the blank line (or closing }) that ends the section.
    header = STRAIN_SECTIONS[args.strain]
    start = next((i for i, l in enumerate(lines) if header in l), None)
    if start is None:
        sys.exit(f"Error: section '{header}' not found in {BANKS_FILE}")
    insert_at = next(
        (i for i, l in enumerate(lines[start + 1:], start + 1)
         if not l.strip() or l.strip() == "}"),
        len(lines),
    )
    lines.insert(insert_at, entry)

    source = "".join(lines)
    try:
        compile(source, BANKS_FILE, "exec")
    except SyntaxError as e:
        sys.exit(f"Error: generated entry breaks {BANKS_FILE}, not writing: {e}")

    with open(BANKS_FILE, "w") as f:
        f.write(source)

    print(f"Registered: {entry.strip()}")


if __name__ == "__main__":
    main()
