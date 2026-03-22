#!/usr/bin/env bash
# Run the audition script on the server.
# Usage: ./scripts/audition.sh
ssh -t root@204.168.163.80 "python3 /opt/eul/scripts/audition.py"
