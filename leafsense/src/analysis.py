"""Time-series comparison, stress prediction, alerts and care suggestions."""
import os
import numpy as np
import pandas as pd

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "stress_model.joblib")
BASE_DAYS = 3
BASE_COLS = ["green_area_pct", "exg_mean", "greenness_ratio", "yellow_pct", "mean_S", "mean_V"]
# Feature columns the ML model is trained on (use the same list in your train script)
DEV_FEATURES = [f"{c}_vs_base" for c in BASE_COLS] + [f"{c}_vs_prev" for c in BASE_COLS] + \
               [f"{c}_vs_ctrl" for c in BASE_COLS]

def add_time_features(df, control_df=None):
    """df: one plant's rows sorted by photo_date. Adds baseline / previous-day / control deviations."""
    df = df.sort_values("photo_date").reset_index(drop=True).copy()
    base = df.head(BASE_DAYS)[BASE_COLS].mean()
    ctrl = None
    if control_df is not None and len(control_df):
        ctrl = control_df.groupby("photo_date")[BASE_COLS].mean()
    for c in BASE_COLS:
        df[f"{c}_vs_base"] = df[c] - base[c]
        df[f"{c}_vs_prev"] = df[c].diff().fillna(0)
        if ctrl is not None:
            m = df["photo_date"].map(ctrl[c])
            df[f"{c}_vs_ctrl"] = (df[c] - m).fillna(0)
        else:
            df[f"{c}_vs_ctrl"] = 0.0
    return df

def predict_stress(df):
    """Use the trained model if present, otherwise a simple rule so the app works from day 1."""
    if len(df) <= BASE_DAYS:
        return np.zeros(len(df), dtype=int)       # still building the baseline
    if os.path.exists(MODEL_PATH):
        import joblib
        return joblib.load(MODEL_PATH).predict(df[DEV_FEATURES]).astype(int)
    votes = ((df["greenness_ratio_vs_base"] < -0.03).astype(int)
             + (df["exg_mean_vs_base"] < -0.01).astype(int)
             + (df["yellow_pct_vs_base"] > 5).astype(int)
             + (df["green_area_pct_vs_prev"] < 0).astype(int)
             + (df["mean_S_vs_base"] < -8).astype(int))
    return (votes >= 2).astype(int).values

def consecutive_alerts(dates, preds, k=2):
    """Alert dates: stress predicted on k consecutive days."""
    out, run_len = [], 0
    for d, p in zip(dates, preds):
        run_len = run_len + 1 if p else 0
        if run_len >= k: out.append(d)
    return out

def care_suggestions(latest):
    tips = []
    if latest["yellow_pct_vs_base"] > 5: tips.append("Yellowing detected: check watering and nitrogen/nutrients.")
    if latest["greenness_ratio_vs_base"] < -0.03: tips.append("Leaves are losing green colour: water the plant and check soil moisture.")
    if latest["green_area_pct_vs_prev"] < 0: tips.append("Canopy shrinking: possible wilting. Inspect soil and move out of harsh midday sun.")
    if latest["mean_V_vs_base"] < -20: tips.append("Plant is darkening: check for fungal spots or overwatering.")
    return tips or ["Check soil moisture and keep conditions steady."]
