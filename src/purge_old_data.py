"""
GDPR storage limitation (Art. 5(1)(e)): delete saved readings older than N days.

  python src/purge_old_data.py            # keep last 30 days
  python src/purge_old_data.py --days 7
"""
import argparse
import csv
from datetime import datetime, timedelta, timezone

from mqtt_common import ROOT

DATA_FILE = ROOT / "data" / "readings.csv"


def main():
    parser = argparse.ArgumentParser(description="Delete readings past the retention period")
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()

    if not DATA_FILE.exists():
        print("No saved readings yet. Nothing to purge.")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    with DATA_FILE.open(newline="") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        rows = list(reader)

    def recent(row):
        try:
            return datetime.fromisoformat(row["ts"]) >= cutoff
        except (ValueError, KeyError):
            return False  # unreadable timestamp: drop it rather than keep it forever

    kept = [r for r in rows if recent(r)]
    with DATA_FILE.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(kept)

    print(f"Retention {args.days} days: kept {len(kept)}, deleted {len(rows) - len(kept)} rows")


if __name__ == "__main__":
    main()
