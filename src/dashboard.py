"""
Terminal dashboard. Subscribes to sensors/# and prints each reading.
Add --save to keep readings in data/readings.csv (see purge_old_data.py for retention).

  Phase 1:  python src/dashboard.py
  Phase 2:  python src/dashboard.py --auth
  Phase 3+: python src/dashboard.py --auth --tls --save
"""
import argparse
import csv
import json
import time

from mqtt_common import ROOT, add_common_args, connect_or_exit

TOPIC_FILTER = "sensors/#"
DATA_FILE = ROOT / "data" / "readings.csv"
FIELDS = ["ts", "sensor_id", "temp_c", "topic"]


def save_row(row):
    DATA_FILE.parent.mkdir(exist_ok=True)
    is_new = not DATA_FILE.exists()
    with DATA_FILE.open("a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="Temperature dashboard")
    add_common_args(parser)
    parser.add_argument("--save", action="store_true", help="append readings to data/readings.csv")
    args = parser.parse_args()

    client = connect_or_exit("dashboard-client", "dashboard", args.auth, args.tls)

    def on_subscribe(c, userdata, mid, reason_codes, properties):
        for rc in reason_codes:
            if rc.is_failure:
                print(f"subscribe to {TOPIC_FILTER} DENIED: {rc}")
            else:
                print(f"subscribed to {TOPIC_FILTER} ({rc})")
        print(f"\n{'time (UTC)':<27}{'sensor':<16}{'temp':>8}")
        print("-" * 51)

    def on_message(c, userdata, msg):
        try:
            data = json.loads(msg.payload)
            temp = float(data["temp_c"])
        except (ValueError, KeyError, TypeError):
            print(f"[{msg.topic}] unreadable payload: {msg.payload[:60]!r}")
            return
        ts, sid = data.get("ts", "?"), data.get("sensor_id", "?")
        flag = "  HIGH" if temp > 27 else ""
        print(f"{ts:<27}{sid:<16}{temp:>6.2f} C{flag}")
        if args.save:
            save_row({"ts": ts, "sensor_id": sid, "temp_c": temp, "topic": msg.topic})

    client.on_subscribe = on_subscribe
    client.on_message = on_message
    client.subscribe(TOPIC_FILTER, qos=1)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\ndashboard stopped")
    finally:
        client.disconnect()
        client.loop_stop()


if __name__ == "__main__":
    main()
