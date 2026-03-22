#!/usr/bin/env bash
# Apply fade-in/fade-out to all audio files in a folder to remove leading/trailing clips.
# Usage: ./fade-samples.sh <folder> [fade_in_ms] [fade_out_ms]
# Defaults: 10ms fade-in, 20ms fade-out

set -e

FOLDER="${1:?Usage: $0 <folder> [fade_in_ms] [fade_out_ms]}"
FADE_IN="${2:-10}"
FADE_OUT="${3:-20}"

FADE_IN_S=$(echo "scale=3; $FADE_IN / 1000" | bc)
FADE_OUT_S=$(echo "scale=3; $FADE_OUT / 1000" | bc)

shopt -s nullglob
files=("$FOLDER"/*.{aif,aiff,wav,mp3,flac,ogg})

if [ ${#files[@]} -eq 0 ]; then
  echo "No audio files found in $FOLDER"
  exit 1
fi

echo "Fading ${#files[@]} files in $FOLDER (in: ${FADE_IN}ms, out: ${FADE_OUT}ms)"

for f in "${files[@]}"; do
  dur=$(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$f" 2>/dev/null)
  fade_out_start=$(echo "$dur - $FADE_OUT_S" | bc)
  tmp="${f}.tmp${f##*.}"
  ffmpeg -y -i "$f" -af "afade=t=in:st=0:d=${FADE_IN_S},afade=t=out:st=${fade_out_start}:d=${FADE_OUT_S}" "$tmp" 2>/dev/null
  mv "$tmp" "$f"
  echo "  $f"
done

echo "Done."
