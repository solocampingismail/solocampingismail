#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m unittest discover -s tests -v
python3 automation/generate_visibility_pack.py
python3 automation/social_publisher.py --dry-run --language en
python3 automation/social_publisher.py --dry-run --language tr
