"""Reproduce a cloud release diagnosis with entirely synthetic data."""
import csv
import json
import sqlite3
from itertools import product
from pathlib import Path

import numpy as np
from scipy.stats import ttest_ind


OUT = Path(__file__).resolve().parent / "outputs"
REGIONS = ("east", "central", "west")
ENDPOINTS = ("catalog", "search")
VERSIONS = ("baseline", "canary")
SPLITS = ("discovery", "confirmation")
REQUESTS_PER_CELL = 1000


def extract_requests():
    rng = np.random.default_rng(614)
    events, traces = [], []
    for region, endpoint, version, split in product(REGIONS, ENDPOINTS, VERSIONS, SPLITS):
        cache_delay = 70 if (region, endpoint, version) == ("east", "catalog", "canary") else 0
        for _ in range(REQUESTS_PER_CELL):
            request_id = len(events) + 1
            cache_base = float(rng.gamma(6, 4))
            service = float(rng.gamma(10, 7)) + (13 if endpoint == "search" else 0)
            network = float(rng.gamma(8, 3)) + (10 if region == "west" else 0)
            cache = cache_base + cache_delay
            elapsed = cache + service + network
            events.append((request_id, region, endpoint, version, split, elapsed, f"demo-{request_id}@example.invalid"))
            traces.append((request_id, cache, service, network, cache_base))

    with sqlite3.connect(":memory:") as db:
        db.executescript("""
            CREATE TABLE request_events (
                id INTEGER PRIMARY KEY, region TEXT, endpoint TEXT, version TEXT,
                split TEXT, elapsed_ms REAL, synthetic_contact TEXT
            );
            CREATE TABLE trace_timings (
                id INTEGER PRIMARY KEY, cache_ms REAL, service_ms REAL,
                network_ms REAL, cache_base_ms REAL
            );
            CREATE TABLE release_manifest (version TEXT PRIMARY KEY, release_group TEXT);
        """)
        db.executemany("INSERT INTO request_events VALUES (?,?,?,?,?,?,?)", events)
        db.executemany("INSERT INTO trace_timings VALUES (?,?,?,?,?)", traces)
        db.executemany("INSERT INTO release_manifest VALUES (?,?)", [(v, v) for v in VERSIONS])
        cursor = db.execute("""
            SELECT e.id, e.region, e.endpoint, m.release_group, e.split, e.elapsed_ms,
                   t.cache_ms, t.service_ms, t.network_ms, t.cache_base_ms
            FROM request_events e
            JOIN trace_timings t ON t.id = e.id
            JOIN release_manifest m ON m.version = e.version
            ORDER BY e.id
        """)
        fields = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

    assert len(rows) == len(events) == len(traces) == 24000
    assert len({row[0] for row in rows}) == len(rows)
    assert "synthetic_contact" not in fields
    assert all(row[5] > 0 and abs(row[5] - sum(row[6:9])) < 1e-8 for row in rows)
    return rows


def analyze(rows):
    groups = {}
    for row in rows:
        groups.setdefault(row[1:5], []).append(row[5:10])
    groups = {key: np.array(records) for key, records in groups.items()}
    assert all(len(group) == REQUESTS_PER_CELL for group in groups.values())
    kpis = []
    for (region, endpoint, version, split), values in groups.items():
        elapsed = values[:, 0]
        kpis.append((region, endpoint, version, split, len(elapsed), float(elapsed.mean()),
                     float(np.percentile(elapsed, 95)), float((elapsed > 220).mean())))

    # Use discovery only to select a region/endpoint. Confirm one comparison in fresh data.
    flagged = max(product(REGIONS, ENDPOINTS), key=lambda segment:
        groups[(*segment, "canary", "discovery")][:, 0].mean()
        - groups[(*segment, "baseline", "discovery")][:, 0].mean())
    canary = groups[(*flagged, "canary", "confirmation")]
    baseline = groups[(*flagged, "baseline", "confirmation")]
    result = ttest_ind(canary[:, 0], baseline[:, 0], equal_var=False)
    ci = result.confidence_interval(confidence_level=0.95)
    differences = canary[:, :4].mean(axis=0) - baseline[:, :4].mean(axis=0)
    assert np.isclose(differences[0], sum(differences[1:]))
    # Replay the same canary requests under the simulator's baseline cache configuration.
    replay_latency = canary[:, 4] + canary[:, 2] + canary[:, 3]
    return kpis, {
        "scope": "Synthetic requests and trace timings, local SQLite and Python",
        "requests": len(rows), "flagged_region": flagged[0], "flagged_endpoint": flagged[1],
        "confirmation_requests_per_arm": len(canary), "mean_gap_ms": float(differences[0]),
        "mean_gap_ci95_ms": [float(ci.low), float(ci.high)],
        "welch_p_value": float(result.pvalue),
        "trace_mean_gaps_ms": dict(zip(("cache", "service", "network"), differences[1:].tolist())),
        "canary_p95_ms": float(np.percentile(canary[:, 0], 95)),
        "rollback_replay_p95_ms": float(np.percentile(replay_latency, 95)),
        "baseline_p95_ms": float(np.percentile(baseline[:, 0], 95)),
    }


def main():
    OUT.mkdir(exist_ok=True)
    kpis, results = analyze(extract_requests())
    with (OUT / "segment_kpis.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["region", "endpoint", "version", "split", "requests", "mean_ms", "p95_ms", "share_over_220_ms"])
        writer.writerows(kpis)
    (OUT / "results.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
