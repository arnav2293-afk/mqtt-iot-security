"""
Simulated temperature sensor. Publishes one JSON reading every few seconds.

  Phase 1:  python src/sensor.py
  Phase 2:  python src/sensor.py --auth
  Phase 3+: python src/sensor.py --auth --tls
"""
import argparse
import json
import random
import time
from datetime import datetime, timezone

from mqtt_common import TOPIC, add_common_args, connect_or_exit


def main():
    parser = argparse.ArgumentParser(description="Simulated temperature sensor")
    add_common_args(parser)
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between readings")
    parser.add_argument("--sensor-id", default="lab1-temp-01")
    args = parser.parse_args()

    client = connect_or_exit("sensor01-client", "sensor", args.auth, args.tls)

    temp = 22.0
    try:
        while True:
            temp = min(30.0, max(15.0, temp + random.uniform(-0.3, 0.3)))
            # Data minimisation: only what the dashboard needs. No location, no person.
            reading = {
                "sensor_id": args.sensor_id,
                "temp_c": round(temp, 2),
                "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            info = client.publish(TOPIC, json.dumps(reading), qos=1)
            info.wait_for_publish(timeout=5)
            print(f"sent -> {TOPIC}: {reading}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nsensor stopped")
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
