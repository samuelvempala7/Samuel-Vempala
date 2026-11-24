"""Recompute the dashboard's headline measures from its embedded sales file."""
import csv
from collections import Counter
from decimal import Decimal
from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent


def main():
    with ZipFile(HERE / "dashboard.twbx") as workbook, workbook.open("Data/sales.csv") as source:
        rows = list(csv.DictReader(TextIOWrapper(source, encoding="utf-8-sig")))
    totals, count = Counter(), Counter()
    for row in rows:
        group = row["customer_type"]
        totals[group] += Decimal(row["total_price"])
        count[group] += 1
    assert len(rows) == len({r["sale_id"] for r in rows}) == 1000
    assert sum(totals.values()) == Decimal("118583.90")
    means = {group: total / count[group] for group, total in totals.items()}
    gap = (means["Member"] / means["Normal"] - 1) * 100
    print(f"{len(rows)} unique records, total receipts {sum(totals.values()):,.2f} CU")
    for group, mean in means.items():
        print(f"{group}: {count[group]} records, mean {mean:.2f} CU")
    print(f"Relative mean gap: {gap:.2f}%")


if __name__ == "__main__":
    main()
