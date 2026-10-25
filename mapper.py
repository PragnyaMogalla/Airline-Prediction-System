#!/usr/bin/env python3
import sys

for line in sys.stdin:
    try:
        line = line.strip()
        if not line or line.startswith("FL_DATE"):
            continue
        
        parts = line.split(",")
        if len(parts) < 16:
            continue
        
        carrier = parts[1].strip().replace('"', '')
        delay_raw = parts[7].strip().replace('"', '')
        cancelled_raw = parts[15].strip().replace('"', '')

        delay_val = float(delay_raw) if delay_raw and delay_raw != "NA" else 0.0
        is_cancelled = int(float(cancelled_raw)) if cancelled_raw and cancelled_raw != "NA" else 0

        if carrier:
            sys.stdout.write("{0}\t1\t{1}\t{2}\n".format(carrier, delay_val, is_cancelled))
    except Exception:
        continue