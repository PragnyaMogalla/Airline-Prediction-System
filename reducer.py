#!/usr/bin/env python3
import sys

current_carrier = None
total_flights = 0
total_delay = 0.0
total_cancelled = 0

for line in sys.stdin:
    try:
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            continue
        carrier, count, delay, cancelled = parts[0], int(parts[1]), float(parts[2]), int(parts[3])
        if current_carrier == carrier:
            total_flights += count
            total_delay += delay
            total_cancelled += cancelled
        else:
            if current_carrier:
                avg_delay = round(total_delay / total_flights, 2) if total_flights else 0.0
                cancel_rate = round((total_cancelled / total_flights) * 100, 2) if total_flights else 0.0
                sys.stdout.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(
                    current_carrier, total_flights, round(total_delay, 2), avg_delay, total_cancelled, cancel_rate
                ))
            current_carrier = carrier
            total_flights = count
            total_delay = delay
            total_cancelled = cancelled
    except Exception:
        continue

if current_carrier:
    avg_delay = round(total_delay / total_flights, 2) if total_flights else 0.0
    cancel_rate = round((total_cancelled / total_flights) * 100, 2) if total_flights else 0.0
    sys.stdout.write("{0}\t{1}\t{2}\t{3}\t{4}\t{5}\n".format(
        current_carrier, total_flights, round(total_delay, 2), avg_delay, total_cancelled, cancel_rate
    ))