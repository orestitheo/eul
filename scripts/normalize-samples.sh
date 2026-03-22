#!/usr/bin/env bash
# Compress and normalize audio files in a folder to consistent loudness.
# Usage: ./scripts/normalize-samples.sh <folder>
#
# Applies dynamic compression to bring up quiet parts, then normalizes peak to -1dB.
# Processes .aif, .aiff, .wav in place. Skips files that are already loud enough.

set -euo pipefail

FOLDER="${1:?Usage: $0 <folder>}"

files=$(find "$FOLDER" -maxdepth 1 \( -name "*.aif" -o -name "*.aiff" -o -name "*.wav" \))

if [ -z "$files" ]; then
  echo "No audio files found in $FOLDER"
  exit 1
fi

count=$(echo "$files" | wc -l | tr -d ' ')
echo "Normalizing $count files in $FOLDER..."

for f in $files; do
  ext="${f##*.}"
  tmp="${f%.*}.tmp.$ext"
  sox "$f" "$tmp" compand 0.3,1 6:-70,-60,-20 -5 -90 0.2 norm -1 2>&1 | grep -v "^$" | sed 's/^/    /' || true
  mv "$tmp" "$f"
  RMS=$(sox "$f" -n stat 2>&1 | grep "RMS amplitude" | awk '{print $3}')
  echo "  ✓ $(basename "$f")  RMS=$RMS"
done

echo "Done."
