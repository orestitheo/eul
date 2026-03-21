#!/usr/bin/env bash
# Run this after adding new samples to the samples/ directory.
# What it does:
#   1. Lowercases all folder names, replaces spaces with underscores
#   2. Strips timestamps like " [2026-03-21 141518]" from filenames
#   3. Lowercases all filenames, replaces spaces with underscores
#
# Safe to run multiple times — only renames if the name would change.

set -euo pipefail

SAMPLES_DIR="$(cd "$(dirname "$0")/../samples" && pwd)"

echo "Processing: $SAMPLES_DIR"

# --- Step 1: Rename directories (bottom-up so nested dirs work correctly) ---
while IFS= read -r -d '' dir; do
  parent="$(dirname "$dir")"
  base="$(basename "$dir")"
  # lowercase + spaces to underscores
  new_base="${base// /_}"
  new_base="$(echo "$new_base" | tr '[:upper:]' '[:lower:]')"
  if [[ "$base" != "$new_base" ]]; then
    echo "  dir:  $base → $new_base"
    mv "$dir" "$parent/$new_base"
  fi
done < <(find "$SAMPLES_DIR" -mindepth 1 -type d -print0 | sort -rz)

# --- Step 2: Rename files ---
while IFS= read -r -d '' file; do
  dir="$(dirname "$file")"
  base="$(basename "$file")"

  # strip timestamp pattern like " [2026-03-21 141518]" anywhere in the name
  new_base="$(echo "$base" | sed -E 's/ \[[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]+\]//g')"
  # lowercase + spaces to underscores
  new_base="${new_base// /_}"
  new_base="$(echo "$new_base" | tr '[:upper:]' '[:lower:]')"

  if [[ "$base" != "$new_base" ]]; then
    echo "  file: $base → $new_base"
    mv "$file" "$dir/$new_base"
  fi
done < <(find "$SAMPLES_DIR" -type f \( -iname "*.wav" -o -iname "*.aif" -o -iname "*.aiff" -o -iname "*.flac" -o -iname "*.mp3" \) -print0)

echo "Done."
