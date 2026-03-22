#!/usr/bin/env bash
# Trigger a manual evolution on the server.
# Usage: ./scripts/evolve.sh [--micro]
ssh root@204.168.163.80 "python3 /opt/eul/scripts/eul/evolve.py ${1:-"--once"}"
