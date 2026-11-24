"""Backtest a 90-day repeat-purchase score on the CDNOW customer cohort."""
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

HERE = Path(__file__).resolve().parent
FEATURES = ["days_since_order", "age_days", "shopping_days", "mean_daily_basket", "active_days_60"]
TARGET = "bought_in_90_days"


def plot_winter_ranking(curves):
    fig, ax = plt.subplots(figsize=(7.2, 3.25), layout="constrained")
    for method, color in [("Recency", "#bb5837"), ("Logistic", "#236979")]:
        counts = curves[method]
        ax.plot(np.arange(1, len(counts) + 1), counts, color=color, label=method, lw=2.2)
    selected = int(len(curves["Logistic"]) * .2)
    count = int(curves["Logistic"][selected - 1])
    ax.scatter(selected, count, color="#172f3b", zorder=3)
    ax.annotate(f"{count} buyers in either list", (selected, count), xytext=(12, -25),
                textcoords="offset points", color="#172f3b")
    ax.set(xlim=(0, 1000), ylim=(0, 330), xlabel="Customers selected, in rank order",
           ylabel="Future buyers found", title="January CDNOW backtest")
    ax.legend(frameon=False, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(HERE / "winter-ranking.png", dpi=170)
    plt.close(fig)


def main():
    raw = pd.read_csv(HERE.parents[1] / "data/CDNOW_sample.txt", sep=r"\s+", header=None,
                      names=["master_id", "customer", "day", "units", "spend"])
    raw["day"] = pd.to_datetime(raw.day, format="%Y%m%d").dt.strftime("%Y-%m-%d")
    query = (HERE / "snapshot.sql").read_text()
    with sqlite3.connect(":memory:") as db:
        raw[["customer", "day", "spend"]].to_sql("orders", db, index=False)
        training, fall, winter = [
            pd.read_sql_query(query, db, params={"cutoff": cutoff})
            for cutoff in ["1997-07-01", "1997-10-01", "1998-01-01"]
        ]
    assert len(raw) == 6919 and len(winter) == winter.customer.nunique() == 2357
    model = make_pipeline(StandardScaler(), LogisticRegression(max_iter=500))
    model.fit(np.log1p(training[FEATURES]), training[TARGET])
    results = []
    for window, frame in [("October 1997", fall), ("January 1998", winter)]:
        label = frame[TARGET].to_numpy()
        score = model.predict_proba(np.log1p(frame[FEATURES]))[:, 1]
        curves = {}
        for method, rank in [("Recency", -frame.days_since_order.to_numpy()), ("Logistic", score)]:
            # A customer ID breaks ties without using future activity.
            order = np.lexsort((frame.customer, -rank))
            top = order[:int(len(frame) * .2)]
            curves[method] = label[order].cumsum()
            rate = label[top].mean()
            results.append(dict(window=window, method=method, customers=len(frame),
                                selected=len(top), repeat_buyers_in_top=int(label[top].sum()),
                                overall_rate=label.mean(), top_fifth_rate=rate,
                                lift=rate / label.mean(), average_precision=average_precision_score(label, rank),
                                brier=brier_score_loss(label, score) if method == "Logistic" else None))
        if window == "January 1998":
            plot_winter_ranking(curves)
    out = pd.DataFrame(results)
    out.to_csv(HERE / "backtest.csv", index=False, float_format="%.5f")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
