"""Measure how often a small intent router can hand off ambiguous banking queries."""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC

HERE = Path(__file__).resolve().parent


def normalized(text):
    return text.str.lower().str.replace(r"[^\w]+", " ", regex=True).str.strip()


def margins(model, frame):
    scores = model.decision_function(frame.text)
    top_two = np.partition(scores, -2, axis=1)[:, -2:]
    return model.classes_[scores.argmax(axis=1)], top_two[:, 1] - top_two[:, 0]


def main():
    data = HERE.parents[1] / "data"
    train = pd.read_csv(data / "train.csv")
    test = pd.read_csv(data / "test.csv")
    assert (len(train), len(test), train.category.nunique()) == (10003, 3080, 77)
    train = train.drop_duplicates(subset="text").copy()
    train = train.loc[~normalized(train.text).duplicated()].copy()
    test = test.loc[~normalized(test.text).isin(normalized(train.text))].copy()
    test = test.loc[~normalized(test.text).duplicated()].copy()
    fit, val = train_test_split(train, test_size=.2, random_state=33, stratify=train.category)
    model = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2),
                          LinearSVC(C=1, random_state=33))
    model.fit(fit.text, fit.category)
    predicted, gap = margins(model, val)
    thresholds = np.arange(0, 1.51, .05)
    candidates = []
    for threshold in thresholds:
        accept = gap >= threshold
        if accept.sum() >= 100 and (predicted[accept] == val.category.to_numpy()[accept]).mean() >= .90:
            candidates.append(threshold)
    if not candidates:
        raise ValueError("No validation threshold met the routing criteria.")
    threshold = min(candidates)
    pred, gap = margins(model, test)
    accept = gap >= threshold
    truth = test.category.to_numpy()
    mistakes = pd.DataFrame({"actual": truth[accept & (pred != truth)], "routed_to": pred[accept & (pred != truth)]})
    mistakes.value_counts().rename("queries").to_csv(HERE / "accepted_misroutes.csv")
    summary = pd.DataFrame([dict(fit=len(fit), validation=len(val), test=len(test),
                                 gap_threshold=threshold, routed=int(accept.sum()),
                                 correct_routed=int((pred[accept] == truth[accept]).sum()),
                                 coverage=accept.mean(), routed_accuracy=(pred[accept] == truth[accept]).mean(),
                                 all_query_accuracy=(pred == truth).mean(), all_query_macro_f1=f1_score(truth, pred, average="macro"))])
    summary.to_csv(HERE / "evaluation.csv", index=False, float_format="%.5f")
    print(summary.to_string(index=False))
    print(mistakes.value_counts().head(5))


if __name__ == "__main__":
    main()
