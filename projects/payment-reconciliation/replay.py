"""Reconcile synthetic payment events with a settlement file at two arrival cutoffs."""
import csv
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent


def records(name):
    with (HERE / name).open(newline="") as stream:
        return list(csv.DictReader(stream))


def main():
    query = (HERE / "reconcile.sql").read_text()
    events = records("events.csv")
    with sqlite3.connect(":memory:") as db:
        db.executescript("""
          CREATE TABLE raw_events (event TEXT NOT NULL, order_id TEXT NOT NULL,
              kind TEXT CHECK(kind IN ('capture','refund')), currency TEXT NOT NULL,
              cents INTEGER NOT NULL CHECK(cents >= 0));
          CREATE TABLE settlements (order_id TEXT, currency TEXT, cents INTEGER NOT NULL,
                                    PRIMARY KEY (order_id, currency));
        """)
        db.executemany("INSERT INTO settlements VALUES (:order_id,:currency,:cents)", records("settlements.csv"))
        insert = "INSERT INTO raw_events VALUES (:event,:order_id,:kind,:currency,:cents)"
        result = []
        for batch in ["1", "2"]:
            arrivals = [row for row in events if row["batch"] == batch]
            db.executemany(insert, arrivals)
            cursor = db.execute(query)
            headers = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            db.executemany(insert, arrivals)
            assert db.execute(query).fetchall() == rows
            result.extend((batch, *row) for row in rows)
    by_order = {(row[0], row[1]): row[-1] for row in result}
    assert by_order["1", "p104"] == "amount mismatch" and by_order["2", "p104"] == "matched"
    assert by_order["2", "p106"] == "conflicting event"
    with (HERE / "exceptions.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["through_batch", *headers])
        writer.writerows(result)
    for row in result:
        print(*row)


if __name__ == "__main__":
    main()
