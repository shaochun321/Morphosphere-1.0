#!/usr/bin/env python3
# v33 tables are prebuilt in outputs/m33.db. This script validates the generated bottom prediction adapter layer.
import subprocess, sys
sys.exit(subprocess.call([sys.executable, 'active/v33/scripts/check_v33.py', '--db', 'outputs/m33.db']))
