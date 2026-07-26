"""
Train a churn classifier.

Feature contract matches what's served through Feast (recency_days,
frequency, lifetime_value, avg_order_value) so there's no train/serve
skew - the online-serving path and the training path agree on what
each feature means.

Label history: the first version trained against `churned` derived
from mart_customer_ltv_rfm's rfm_segment (At Risk/Lost). That label is
built from r_score, an ntile() over recency_days - so it was nearly a
deterministic function of a feature we were training on. Result: 1.00
precision/recall/f1 across the board, which is a leakage signature,
not a good model.

Fixed by training against ml/build_churn_training_set.py's output
instead: a genuine forward-looking holdout where features come from
orders before a cutoff and the label is "did they order again in the
90 days after it" - a completely different data slice per row, so the
label can't be reconstructed from the features by definition.
"""
import os
import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "churn_training_set.parquet")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "churn_model.joblib")
FEATURE_COLS = ["recency_days", "frequency", "lifetime_value", "avg_order_value"]

df = pd.read_parquet(DATA_PATH)
X = df[FEATURE_COLS].fillna(0)
y = df["churned"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", LogisticRegression(max_iter=1000)),
])
pipeline.fit(X_train, y_train)

y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
y_pred = pipeline.predict(X_test)

print("AUC:", roc_auc_score(y_test, y_pred_proba))
print(classification_report(y_test, y_pred))

joblib.dump({"pipeline": pipeline, "feature_cols": FEATURE_COLS}, MODEL_PATH)
print(f"Model saved to {MODEL_PATH}")
