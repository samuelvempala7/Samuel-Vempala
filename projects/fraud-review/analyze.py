"""End-of-day review queues on a seeded, deliberately imperfect transaction simulator."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.ensemble import HistGradientBoostingClassifier

HERE = Path(__file__).resolve().parent
FEATURES = ["amount", "account_days", "new_device", "cross_border", "recent_attempts"]


def ledger(seed=45):
    rng = np.random.default_rng(seed)
    day = np.repeat(np.arange(100), 500)
    n = len(day)
    amount = rng.lognormal(3.35, 1.05, n).round(2)
    age = rng.geometric(.008, n)
    device = rng.binomial(1, .12 + .08 * (day >= 80), n)
    border = rng.binomial(1, .18, n)
    attempts = rng.poisson(.7 + .35 * device, n)
    # The higher new-device share in the last 20 days creates a mix shift.
    log_odds = (-5.25 + .55 * np.log1p(amount / 70) + 1.2 * device + .85 * border
                + 1.1 * (age < 15) + .60 * attempts + .75 * device * border)
    return pd.DataFrame(dict(day=day, txn=np.arange(n), amount=amount, account_days=age,
                             new_device=device, cross_border=border, recent_attempts=attempts,
                             fraud=rng.binomial(1, expit(log_odds))))


def main():
    frame = ledger()
    # Leave a 10-day label-maturity buffer before the final 20-day replay.
    train, test = frame.loc[frame.day < 70], frame.loc[frame.day >= 80].copy()
    model = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=12, min_samples_leaf=80,
                                           l2_regularization=2, random_state=45, early_stopping=False)
    model.fit(train[FEATURES], train.fraud)
    test["model"] = model.predict_proba(test[FEATURES])[:, 1]
    results = []
    for capacity in [5, 10, 20, 40]:
        for policy, score in [("Largest amount", "amount"), ("Model", "model")]:
            ordered = test.sort_values(["day", score, "txn"], ascending=[True, False, True])
            picks = ordered.groupby("day", sort=False).head(capacity)
            caught = int(picks.fraud.sum())
            results.append(dict(policy=policy, daily_capacity=capacity, reviews=len(picks),
                                caught=caught, false_alerts=len(picks) - caught,
                                total_fraud=int(test.fraud.sum()), precision=caught / len(picks),
                                recall=caught / test.fraud.sum()))
    table = pd.DataFrame(results)
    table.to_csv(HERE / "queues.csv", index=False, float_format="%.5f")
    fig, ax = plt.subplots(figsize=(6.8, 3.4), layout="constrained")
    for policy, color in [("Model", "#206a73"), ("Largest amount", "#a9583b")]:
        points = table.loc[table.policy.eq(policy)]
        ax.plot(points.daily_capacity, points.recall * 100, marker="o", label=policy, color=color)
    ax.set(xticks=[5, 10, 20, 40], xlabel="Daily review slots", ylabel="Labeled fraud caught (%)",
           title="What does a larger review queue buy?")
    ax.set_ylim(bottom=0)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.savefig(HERE / "capacity.png", dpi=160)
    plt.close(fig)
    print(table.to_string(index=False))


if __name__ == "__main__":
    main()
