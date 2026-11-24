"""Compare the risk ranking and probability accuracy of two historical benchmarks."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

HERE = Path(__file__).resolve().parent
CATEGORIES = ["laufkont", "moral", "sparkont", "verw"]
NUMERIC = ["laufzeit", "hoehe"]


def main():
    df = pd.read_csv(HERE.parents[1] / "data/SouthGermanCredit.asc", sep=r"\s+")
    bad = df.kredit.eq(0).astype(int)
    assert len(df) == 1000 and bad.sum() == 300
    train_x, test_x, train_y, test_y = train_test_split(
        df[CATEGORIES + NUMERIC], bad, test_size=.30, stratify=bad, random_state=17)
    preprocess = ColumnTransformer([
        ("account", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORIES),
        ("numeric", StandardScaler(), NUMERIC),
    ])
    models = {"Logistic": LogisticRegression(max_iter=1000),
              "Forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=12, random_state=17)}
    scores = {"Sample rate": np.full(len(test_y), train_y.mean())}
    for name, estimator in models.items():
        pipeline = make_pipeline(preprocess, estimator)
        pipeline.fit(train_x, train_y)
        scores[name] = pipeline.predict_proba(test_x)[:, 1]
    metrics = pd.DataFrame([dict(model=name, test_records=len(test_y), auc=roc_auc_score(test_y, p),
                                 brier=brier_score_loss(test_y, p)) for name, p in scores.items()])
    metrics.to_csv(HERE / "scores.csv", index=False, float_format="%.5f")
    bins = []
    fig, ax = plt.subplots(figsize=(6.5, 4.6), layout="constrained")
    ax.plot([0, 1], [0, 1], color="#84919a", linestyle="--", label="Perfect agreement")
    for name, color in [("Logistic", "#216a88"), ("Forest", "#ba562d")]:
        p = scores[name]
        frame = pd.DataFrame({"score": p, "bad": test_y.to_numpy()})
        grouped = frame.groupby(pd.qcut(p, 5, duplicates="drop"), observed=True)
        table = grouped.agg(predicted=("score", "mean"), observed=("bad", "mean"),
                            records=("bad", "size"), adverse_cases=("bad", "sum")).reset_index(drop=True)
        table["model"] = name
        bins.append(table)
        ax.plot(table.predicted, table.observed, marker="o", label=name, color=color)
    ax.set(xlim=(0, .85), ylim=(0, .85), xlabel="Mean predicted probability",
           ylabel="Observed adverse repayment share", title="How well do the score bands line up?")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(HERE / "calibration.png", dpi=160)
    plt.close(fig)
    pd.concat(bins).to_csv(HERE / "bands.csv", index=False, float_format="%.5f")
    print(metrics.to_string(index=False))


if __name__ == "__main__":
    main()
