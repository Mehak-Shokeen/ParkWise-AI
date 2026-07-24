"""
=============================================================================
Smart Parking Intelligence System - Model Training Pipeline
=============================================================================
Author  : Hackathon Team
Dataset : Bangalore Parking Violations (Jan–May 2024)
Purpose : Train ML models to predict illegal parking severity level
=============================================================================
"""

# ── Standard Imports ─────────────────────────────────────────────────────────
import warnings
warnings.filterwarnings("ignore")

import os, pickle, json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from datetime import datetime

# ── Sklearn ───────────────────────────────────────────────────────────────────
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, ExtraTreesClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, MinMaxScaler
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score, recall_score,
    classification_report, confusion_matrix, ConfusionMatrixDisplay
)
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 ── Data Loading & Raw EDA
# ══════════════════════════════════════════════════════════════════════════════



SEED = 42
np.random.seed(SEED)

def load_raw_data(path: str) -> pd.DataFrame:
    """Load raw CSV and do initial type coercion."""
    print("[1/9] Loading raw dataset …")
    df = pd.read_csv(path)
    df["created_datetime"] = pd.to_datetime(df["created_datetime"], format="mixed", utc=True)
    print(f"      Shape: {df.shape}")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 ── Feature Engineering from Raw Data
# ══════════════════════════════════════════════════════════════════════════════

# Violation-type → severity multiplier mapping
VIOLATION_SEVERITY = {
    "WRONG PARKING":                       1,
    "NO PARKING":                          2,
    "PARKING IN A MAIN ROAD":             3,
    "PARKING ON FOOTPATH":                 3,
    "DOUBLE PARKING":                      3,
    "PARKING NEAR BUSTOP/SCHOOL/HOSPITAL ETC": 4,
}

VEHICLE_WEIGHT = {
    "SCOOTER": 1, "MOPED": 1, "MOTOR CYCLE": 1,
    "PASSENGER AUTO": 2, "GOODS AUTO": 2,
    "CAR": 2, "VAN": 2, "LGV": 3,
    "MAXI-CAB": 3, "PRIVATE BUS": 4,
    "BUS": 4, "TRUCK": 4,
}

def parse_violation_list(vtype_str: str) -> list:
    """Parse '[\"NO PARKING\",\"WRONG PARKING\"]' → ['NO PARKING','WRONG PARKING']."""
    try:
        import re
        items = re.findall(r'"([^"]+)"', str(vtype_str))
        return items
    except Exception:
        return []

def violation_score(vtype_str: str) -> int:
    items = parse_violation_list(vtype_str)
    return sum(VIOLATION_SEVERITY.get(v, 1) for v in items) if items else 1

def location_type_from_junction(junction: str) -> str:
    """Infer location_type from junction name."""
    junc = str(junction).lower()
    if "no junction" in junc:
        return "Street"
    elif any(k in junc for k in ["metro", "station", "bus"]):
        return "Transit Hub"
    elif any(k in junc for k in ["market", "plaza", "mall"]):
        return "Commercial Zone"
    elif any(k in junc for k in ["hospital", "school", "college"]):
        return "Institutional Zone"
    else:
        return "Junction"

def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract temporal features from created_datetime."""
    df["hour"]        = df["created_datetime"].dt.hour
    df["day_of_week"] = df["created_datetime"].dt.dayofweek   # 0=Mon
    df["month"]       = df["created_datetime"].dt.month
    df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)

    def time_of_day(h):
        if   h < 6:  return "Night"
        elif h < 12: return "Morning"
        elif h < 17: return "Afternoon"
        elif h < 21: return "Evening"
        else:        return "Night"

    df["time_of_day"] = df["hour"].map(time_of_day)
    return df

def compute_hotspot_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate violation counts per grid cell (≈250 m) to simulate
    historical_violation_count and illegal_vehicle_count.
    """
    df["lat_grid"] = (df["latitude"]  / 0.002).round(0)
    df["lon_grid"] = (df["longitude"] / 0.002).round(0)

    # historical violation count per grid
    grid_counts = (
        df.groupby(["lat_grid","lon_grid"])
          .size()
          .reset_index(name="historical_violation_count")
    )
    df = df.merge(grid_counts, on=["lat_grid","lon_grid"], how="left")
    return df

def synthesize_simulation_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Synthesize domain-realistic continuous features that the original
    dataset does not carry (traffic_volume, average_speed, parking_occupancy,
    road_width, nearby_event).  Values are seeded deterministically so the
    pipeline is reproducible.
    """
    rng = np.random.default_rng(SEED)
    n = len(df)

    # ── vehicle weight score ──────────────────────────────────────────────────
    df["vehicle_weight"] = df["vehicle_type"].map(VEHICLE_WEIGHT).fillna(2)

    # ── violation severity score ──────────────────────────────────────────────
    df["violation_score"] = df["violation_type"].map(violation_score)

    # ── base traffic volume (peak hours  → higher) ────────────────────────────
    peak_mult = np.where(df["hour"].between(8,10) | df["hour"].between(17,20), 1.4, 1.0)
    df["traffic_volume"] = (
        rng.integers(200, 800, n) * peak_mult
        + df["historical_violation_count"].clip(upper=200) * 0.5
    ).astype(int).clip(100, 2000)

    # ── average_speed (inversely related to traffic volume) ───────────────────
    df["average_speed"] = (
        60 - df["traffic_volume"] / 50
        + rng.normal(0, 3, n)
    ).clip(5, 60).round(1)

    # ── parking_occupancy (% 0–100) ───────────────────────────────────────────
    df["parking_occupancy"] = (
        40
        + df["violation_score"] * 5
        + df["is_weekend"] * 8
        + rng.normal(0, 10, n)
    ).clip(0, 100).round(1)

    # ── road_width in metres ──────────────────────────────────────────────────
    road_map = {
        "Junction": 14.0, "Commercial Zone": 12.0, "Transit Hub": 16.0,
        "Institutional Zone": 12.0, "Street": 8.0,
    }
    df["road_width"] = (
        df["location_type"].map(road_map).fillna(10.0)
        + rng.normal(0, 1.5, n)
    ).clip(4, 24).round(1)

    # ── nearby_event binary flag ──────────────────────────────────────────────
    # Weekends + certain hours spike the chance of a nearby event
    event_prob = np.where(df["is_weekend"], 0.3, 0.1)
    df["nearby_event"] = rng.binomial(1, event_prob).astype(int)

    # ── illegal_vehicle_count ─────────────────────────────────────────────────
    df["illegal_vehicle_count"] = (
        df["vehicle_weight"]
        + df["violation_score"]
        + rng.integers(0, 5, n)
        + df["nearby_event"] * 2
    ).clip(1, 20)

    return df

def derive_delay_score(df: pd.DataFrame) -> pd.DataFrame:
    """delay_score = inverse speed × traffic density proxy."""
    df["delay_score"] = (
        (60 - df["average_speed"]) / 60         # 0–1  (high = slow)
        * (df["traffic_volume"] / 2000)          # 0–1
        * 100
    ).clip(0, 100).round(2)
    return df

def assign_severity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Derive target variable severity_level using a rule-based composite
    that reflects ground-truth domain logic.
    """
    score = (
        df["violation_score"]            * 0.30
        + df["vehicle_weight"]           * 0.10
        + df["illegal_vehicle_count"]    * 0.15
        + df["traffic_volume"]     / 200 * 0.15
        + df["parking_occupancy"]  / 20  * 0.10
        + (1 - df["average_speed"] / 60) * 0.10
        + df["nearby_event"]             * 0.05
        + np.log1p(df["historical_violation_count"]) * 0.05
    )
    # Normalise to 0-100
    score = (score - score.min()) / (score.max() - score.min()) * 100

    def classify(s):
        if s < 25:  return "Low"
        if s < 50:  return "Medium"
        if s < 75:  return "High"
        return "Critical"

    df["severity_score"] = score.round(2)
    df["severity_level"] = score.map(classify)
    return df

def compute_pci(df: pd.DataFrame, scaler: MinMaxScaler = None) -> pd.DataFrame:
    """
    Parking Congestion Index:
      PCI = 0.4×norm(illegal_vehicle_count) + 0.3×norm(traffic_volume)
            + 0.2×norm(delay_score) + 0.1×norm(parking_occupancy)
    """
    cols = ["illegal_vehicle_count", "traffic_volume", "delay_score", "parking_occupancy"]
    if scaler is None:
        scaler = MinMaxScaler()
        normed = scaler.fit_transform(df[cols])
    else:
        normed = scaler.transform(df[cols])

    weights = np.array([0.4, 0.3, 0.2, 0.1])
    pci = (normed * weights).sum(axis=1) * 100

    df["pci_score"] = pci.round(2)

    def pci_class(p):
        if p <= 25: return "Low"
        if p <= 50: return "Moderate"
        if p <= 75: return "High"
        return "Critical"

    df["pci_category"] = df["pci_score"].map(pci_class)
    return df, scaler


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 ── Full Feature Pipeline
# ══════════════════════════════════════════════════════════════════════════════

FEATURE_COLS = [
    "location_type", "illegal_vehicle_count", "traffic_volume",
    "average_speed", "parking_occupancy", "road_width",
    "historical_violation_count", "nearby_event",
    "day_of_week", "time_of_day",
    # Engineered extras
    "violation_score", "vehicle_weight", "delay_score",
    "is_weekend", "hour", "pci_score",
]

TARGET_COL = "severity_level"

def build_features(df_raw: pd.DataFrame):
    """End-to-end feature engineering → returns model-ready X, y."""
    print("[2/9] Engineering features …")
    df = df_raw.copy()
    df = add_time_features(df)
    df = compute_hotspot_features(df)
    df["location_type"] = df["junction_name"].map(location_type_from_junction)
    df = synthesize_simulation_features(df)
    df = derive_delay_score(df)
    df = assign_severity(df)
    df, pci_scaler = compute_pci(df)
    print(f"      Severity distribution:\n{df[TARGET_COL].value_counts().to_string()}")
    return df, pci_scaler


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 ── Preprocessing (Encode + Scale)
# ══════════════════════════════════════════════════════════════════════════════

CATEGORICAL_COLS = ["location_type", "time_of_day"]
NUMERIC_COLS = [c for c in FEATURE_COLS if c not in CATEGORICAL_COLS]

def preprocess(df: pd.DataFrame, encoders: dict = None, fit: bool = True):
    """
    Label-encode categoricals, impute NaN, return (X_array, encoders_dict).
    Set fit=False + pass encoders for inference.
    """
    X = df[FEATURE_COLS].copy()
    if encoders is None:
        encoders = {}

    for col in CATEGORICAL_COLS:
        if fit:
            le = LabelEncoder()
            X[col] = le.fit_transform(X[col].astype(str))
            encoders[col] = le
        else:
            le = encoders[col]
            X[col] = X[col].astype(str).map(
                lambda v: le.transform([v])[0] if v in le.classes_ else -1
            )

    # Impute numeric NaN
    for col in NUMERIC_COLS:
        if X[col].isna().any():
            X[col] = X[col].fillna(X[col].median())

    return X.values, encoders


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 ── Model Training
# ══════════════════════════════════════════════════════════════════════════════

LABEL_ORDER = ["Low", "Medium", "High", "Critical"]

def encode_target(y_series: pd.Series):
    le = LabelEncoder()
    le.fit(LABEL_ORDER)
    return le.transform(y_series), le

def train_models(X_train, y_train):
    """Train RandomForest, GradientBoosting, ExtraTrees."""
    print("[4/9] Training models …")
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=3,
            class_weight="balanced", n_jobs=-1, random_state=SEED
        ),
        "GradientBoosting": GradientBoostingClassifier(
            n_estimators=200, learning_rate=0.08, max_depth=5,
            min_samples_leaf=5, random_state=SEED
        ),
        "ExtraTrees": ExtraTreesClassifier(
            n_estimators=200, max_depth=14, min_samples_leaf=3,
            class_weight="balanced", n_jobs=-1, random_state=SEED
        ),
    }
    trained = {}
    for name, model in models.items():
        print(f"      Fitting {name} …", end=" ", flush=True)
        model.fit(X_train, y_train)
        print("done")
        trained[name] = model
    return trained


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 ── Evaluation
# ══════════════════════════════════════════════════════════════════════════════

def evaluate_models(models: dict, X_test, y_test, label_encoder) -> pd.DataFrame:
    """Compute Accuracy, Precision, Recall, F1 for each model."""
    print("[5/9] Evaluating models …")
    rows = []
    for name, model in models.items():
        y_pred = model.predict(X_test)
        rows.append({
            "Model":     name,
            "Accuracy":  round(accuracy_score(y_test, y_pred), 4),
            "Precision": round(precision_score(y_test, y_pred, average="weighted", zero_division=0), 4),
            "Recall":    round(recall_score(y_test, y_pred, average="weighted", zero_division=0), 4),
            "F1_Score":  round(f1_score(y_test, y_pred, average="weighted", zero_division=0), 4),
        })
        print(f"\n      {name}")
        print(classification_report(
            label_encoder.inverse_transform(y_test),
            label_encoder.inverse_transform(y_pred),
            target_names=LABEL_ORDER
        ))
    return pd.DataFrame(rows)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 ── Plotting
# ══════════════════════════════════════════════════════════════════════════════

def save_confusion_matrices(models, X_test, y_test, label_encoder, out_dir):
    """Save one confusion matrix image per model."""
    print("[6/9] Saving confusion matrices …")
    for name, model in models.items():
        y_pred = model.predict(X_test)
        cm = confusion_matrix(y_test, y_pred)
        fig, ax = plt.subplots(figsize=(7, 5))
        disp = ConfusionMatrixDisplay(cm, display_labels=LABEL_ORDER)
        disp.plot(ax=ax, colorbar=True, cmap="Blues")
        ax.set_title(f"Confusion Matrix — {name}", fontsize=13, fontweight="bold")
        plt.tight_layout()
        plt.savefig(f"{out_dir}/confusion_matrix_{name.lower()}.png", dpi=150)
        plt.close()

def save_feature_importance(models, feature_names, out_dir):
    """Save feature importance bar charts."""
    print("[7/9] Saving feature importance plots …")
    colors = {"RandomForest": "#2196F3", "GradientBoosting": "#FF5722", "ExtraTrees": "#4CAF50"}
    for name, model in models.items():
        fi = pd.Series(model.feature_importances_, index=feature_names)
        fi = fi.sort_values(ascending=True).tail(15)
        fig, ax = plt.subplots(figsize=(9, 6))
        fi.plot(kind="barh", ax=ax, color=colors.get(name, "#9C27B0"))
        ax.set_title(f"Feature Importance — {name}", fontsize=13, fontweight="bold")
        ax.set_xlabel("Importance Score")
        ax.grid(axis="x", alpha=0.3)
        plt.tight_layout()
        plt.savefig(f"{out_dir}/feature_importance_{name.lower()}.png", dpi=150)
        plt.close()

def save_eda_plots(df, out_dir):
    """Save EDA overview charts."""
    print("[3/9] Saving EDA plots …")
    fig, axes = plt.subplots(2, 3, figsize=(16, 9))
    fig.suptitle("Smart Parking — Exploratory Data Analysis", fontsize=15, fontweight="bold")

    palette = ["#2196F3", "#FF5722", "#4CAF50", "#FF9800"]

    # 1. Severity distribution
    ax = axes[0, 0]
    counts = df["severity_level"].value_counts().reindex(LABEL_ORDER)
    counts.plot(kind="bar", ax=ax, color=palette, edgecolor="white")
    ax.set_title("Severity Level Distribution")
    ax.set_xlabel(""); ax.tick_params(axis="x", rotation=0)
    for p in ax.patches:
        ax.annotate(f"{int(p.get_height()):,}", (p.get_x()+p.get_width()/2, p.get_height()),
                    ha="center", va="bottom", fontsize=8)

    # 2. Violations by hour
    ax = axes[0, 1]
    df.groupby("hour").size().plot(ax=ax, color="#2196F3", linewidth=2, marker="o", markersize=3)
    ax.set_title("Violations by Hour of Day"); ax.set_xlabel("Hour"); ax.set_ylabel("Count")

    # 3. Violations by day
    ax = axes[0, 2]
    days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    df.groupby("day_of_week").size().reindex(range(7)).plot(kind="bar", ax=ax, color="#FF5722")
    ax.set_title("Violations by Day of Week"); ax.set_xticklabels(days, rotation=0)

    # 4. PCI category
    ax = axes[1, 0]
    df["pci_category"].value_counts().reindex(["Low","Moderate","High","Critical"]).plot(
        kind="bar", ax=ax, color=palette, edgecolor="white")
    ax.set_title("Parking Congestion Index (PCI)"); ax.tick_params(axis="x", rotation=0)

    # 5. Traffic volume by severity
    ax = axes[1, 1]
    df.boxplot(column="traffic_volume", by="severity_level", ax=ax,
               positions=range(len(LABEL_ORDER)),
               boxprops=dict(color="#2196F3"), medianprops=dict(color="red"))
    ax.set_xticklabels(LABEL_ORDER, rotation=0); ax.set_title("Traffic Volume by Severity")
    plt.sca(ax); plt.title("Traffic Volume by Severity"); plt.suptitle("")

    # 6. Location type
    ax = axes[1, 2]
    df["location_type"].value_counts().head(5).plot(kind="barh", ax=ax, color="#9C27B0")
    ax.set_title("Top Location Types")

    plt.tight_layout()
    plt.savefig(f"{out_dir}/eda_overview.png", dpi=150)
    plt.close()

def save_model_comparison(metrics_df, out_dir):
    """Bar chart comparing models on all 4 metrics."""
    fig, ax = plt.subplots(figsize=(10, 5))
    x = np.arange(len(metrics_df))
    width = 0.2
    cols   = ["Accuracy","Precision","Recall","F1_Score"]
    colors = ["#2196F3","#FF5722","#4CAF50","#FF9800"]
    for i, (col, c) in enumerate(zip(cols, colors)):
        ax.bar(x + i*width, metrics_df[col], width, label=col, color=c, edgecolor="white")
    ax.set_xticks(x + 1.5*width)
    ax.set_xticklabels(metrics_df["Model"])
    ax.set_ylim(0, 1.1); ax.set_ylabel("Score")
    ax.set_title("Model Performance Comparison", fontsize=13, fontweight="bold")
    ax.legend(); ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(f"{out_dir}/model_comparison.png", dpi=150)
    plt.close()


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 ── Save Artefacts
# ══════════════════════════════════════════════════════════════════════════════

def save_artefacts(best_model, best_name, label_encoder, encoders, pci_scaler, out_dir):
    """Pickle the full model bundle needed for inference."""
    print("[8/9] Saving model artefacts …")
    bundle = {
        "model":         best_model,
        "model_name":    best_name,
        "label_encoder": label_encoder,
        "cat_encoders":  encoders,
        "pci_scaler":    pci_scaler,
        "feature_cols":  FEATURE_COLS,
        "label_order":   LABEL_ORDER,
        "trained_at":    datetime.now().isoformat(),
    }
    pkl_path = f"{out_dir}/model.pkl"
    with open(pkl_path, "wb") as f:
        pickle.dump(bundle, f)
    print(f"      Saved → {pkl_path}")
    return pkl_path


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 ── Main
# ══════════════════════════════════════════════════════════════════════════════

def main():
    RAW_DATA_PATH = "/mnt/user-data/uploads/jan_to_may_police_violation_anonymized791b166.csv"
    OUTPUT_DIR    = "/mnt/user-data/outputs"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # ── Load & engineer features ────────────────────────────────────────────
    df_raw = load_raw_data(RAW_DATA_PATH)
    df, pci_scaler = build_features(df_raw)
    save_eda_plots(df, OUTPUT_DIR)

    # ── Prepare X, y ────────────────────────────────────────────────────────
    X_raw, encoders = preprocess(df, fit=True)
    y_raw, label_encoder = encode_target(df[TARGET_COL])

    X_tr, X_te, y_tr, y_te = train_test_split(
        X_raw, y_raw, test_size=0.20, stratify=y_raw, random_state=SEED
    )
    print(f"      Train: {X_tr.shape}, Test: {X_te.shape}")

    # ── Train ────────────────────────────────────────────────────────────────
    models = train_models(X_tr, y_tr)

    # ── Evaluate ─────────────────────────────────────────────────────────────
    metrics_df = evaluate_models(models, X_te, y_te, label_encoder)
    print("\n── Model Metrics Summary ──────────────────────────────")
    print(metrics_df.to_string(index=False))

    # ── Plots ────────────────────────────────────────────────────────────────
    save_confusion_matrices(models, X_te, y_te, label_encoder, OUTPUT_DIR)
    save_feature_importance(models, FEATURE_COLS, OUTPUT_DIR)
    save_model_comparison(metrics_df, OUTPUT_DIR)

    # ── Best model ───────────────────────────────────────────────────────────
    best_row  = metrics_df.loc[metrics_df["F1_Score"].idxmax()]
    best_name = best_row["Model"]
    best_model = models[best_name]
    print(f"\n[Best Model] {best_name}  F1={best_row['F1_Score']:.4f}  "
          f"Acc={best_row['Accuracy']:.4f}")

    # ── Save ─────────────────────────────────────────────────────────────────
    save_artefacts(best_model, best_name, label_encoder, encoders, pci_scaler, OUTPUT_DIR)

    # ── Save metrics CSV ─────────────────────────────────────────────────────
    metrics_df.to_csv(f"{OUTPUT_DIR}/model_metrics.csv", index=False)

    print("\n[9/9] All outputs written to", OUTPUT_DIR)
    return metrics_df, best_name

if __name__ == "__main__":
    metrics_df, best_name = main()
