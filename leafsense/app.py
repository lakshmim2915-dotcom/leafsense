import os
from datetime import date
import pandas as pd
import streamlit as st

from src import auth
from src.db import q, run
from src.features import extract_features, FEATURE_NAMES
from src.analysis import add_time_features, predict_stress, consecutive_alerts, care_suggestions

st.set_page_config(page_title="Leaf Sense", page_icon="🌿", layout="wide")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "uploads")

# ---------- login / register ----------
def auth_page():
    st.title("🌿 Leaf Sense")
    st.caption("Pre-symptom plant stress detection from time-lapse images")
    tab_in, tab_up = st.tabs(["Log in", "Register"])
    with tab_in:
        u = st.text_input("Username", key="li_u")
        p = st.text_input("Password", type="password", key="li_p")
        if st.button("Log in"):
            user = auth.login(u, p)
            if user:
                st.session_state.user = user; st.rerun()
            else:
                st.error("Wrong username or password.")
    with tab_up:
        u = st.text_input("Username", key="su_u")
        e = st.text_input("Email", key="su_e")
        p = st.text_input("Password (min 8 chars)", type="password", key="su_p")
        if st.button("Create account"):
            ok, msg = auth.register(u, e, p)
            (st.success if ok else st.error)(msg)

if "user" not in st.session_state:
    auth_page(); st.stop()

user = st.session_state.user
st.sidebar.title(f"👤 {user['username']}")
page = st.sidebar.radio("Menu", ["Dashboard", "Upload photo", "My plants"])
if st.sidebar.button("Log out"):
    del st.session_state["user"]; st.rerun()

plants = q("SELECT * FROM plants WHERE user_id=:u ORDER BY id", u=user["id"])
pname = {p["id"]: f"{p['name']}{' (control)' if p['is_control'] else ''}" for p in plants}

# ---------- My plants ----------
if page == "My plants":
    st.header("My plants")
    with st.form("add_plant", clear_on_submit=True):
        name = st.text_input("Plant name (e.g. Pot 1)")
        species = st.text_input("Species (e.g. Tomato)")
        ctrl = st.checkbox("This is a healthy CONTROL plant (always watered)")
        if st.form_submit_button("Add plant") and name:
            run("INSERT INTO plants(user_id,name,species,is_control) VALUES(:u,:n,:s,:c)",
                u=user["id"], n=name, s=species, c=ctrl)
            st.rerun()
    if plants:
        st.dataframe(pd.DataFrame(plants)[["id", "name", "species", "is_control"]], hide_index=True)
        st.subheader("Record stress dates (used for training / lead-time)")
        pid = st.selectbox("Plant", list(pname), format_func=pname.get, key="ev_p")
        c1, c2 = st.columns(2)
        onset = c1.date_input("Stress onset (stopped watering)", value=None)
        vis = c2.date_input("First visible symptom", value=None)
        if st.button("Save dates"):
            run("REPLACE INTO plant_events(plant_id,stress_onset,first_visible_symptom) VALUES(:p,:o,:v)",
                p=pid, o=onset, v=vis)
            st.success("Saved.")

# ---------- Upload ----------
elif page == "Upload photo":
    st.header("Upload today's photo")
    if not plants:
        st.info("Add a plant first under **My plants**."); st.stop()
    pid = st.selectbox("Plant", list(pname), format_func=pname.get)
    d = st.date_input("Photo date", value=date.today())
    f = st.file_uploader("Photo (same position & lighting every day)", type=["jpg", "jpeg", "png"])
    if f and st.button("Analyse & save"):
        folder = os.path.join(UPLOAD_DIR, str(user["id"]), str(pid)); os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{d.isoformat()}.jpg")
        with open(path, "wb") as out: out.write(f.getbuffer())
        try:
            feats = extract_features(path)
        except ValueError as e:
            st.error(str(e)); st.stop()
        cols = ",".join(FEATURE_NAMES); vals = ",".join(f":{n}" for n in FEATURE_NAMES)
        upd = ",".join(f"{n}=VALUES({n})" for n in FEATURE_NAMES)
        run(f"INSERT INTO daily_features(plant_id,photo_date,image_path,{cols}) "
            f"VALUES(:pid,:d,:path,{vals}) ON DUPLICATE KEY UPDATE image_path=VALUES(image_path),{upd}",
            pid=pid, d=d, path=path, **{k: float(v) for k, v in feats.items()})
        st.success("Saved. Open the Dashboard to see the analysis.")
        st.image(path, width=320)

# ---------- Dashboard ----------
else:
    st.header("Dashboard")
    if not plants:
        st.info("Add a plant first under **My plants**."); st.stop()
    pid = st.selectbox("Plant", list(pname), format_func=pname.get)
    rows = q("SELECT * FROM daily_features WHERE plant_id=:p", p=pid)
    if not rows:
        st.info("No photos yet."); st.stop()
    df = pd.DataFrame(rows); df["photo_date"] = pd.to_datetime(df["photo_date"]).dt.date
    ctrl_rows = q("""SELECT f.* FROM daily_features f JOIN plants p ON p.id=f.plant_id
                     WHERE p.user_id=:u AND p.is_control=1 AND p.id<>:p""", u=user["id"], p=pid)
    ctrl = pd.DataFrame(ctrl_rows) if ctrl_rows else None
    if ctrl is not None: ctrl["photo_date"] = pd.to_datetime(ctrl["photo_date"]).dt.date
    df = add_time_features(df, ctrl)
    df["stress_pred"] = predict_stress(df)
    for _, r in df.iterrows():
        run("UPDATE daily_features SET stress_pred=:s WHERE id=:i", s=int(r["stress_pred"]), i=int(r["id"]))
    alerts = consecutive_alerts(df["photo_date"], df["stress_pred"])

    if len(df) <= 3:
        st.info("Building baseline: upload at least 4 days of photos to start detection.")
    elif alerts:
        st.error(f"⚠️ Stress alert since {alerts[0]} (stress predicted on consecutive days)")
        for d_ in alerts:
            run("INSERT IGNORE INTO alerts(plant_id,alert_date,message) VALUES(:p,:d,:m)",
                p=pid, d=d_, m="Early stress detected")
        st.subheader("Care suggestions")
        for t in care_suggestions(df.iloc[-1]): st.write("•", t)
    else:
        st.success("✅ No stress detected.")
        ev = q("SELECT * FROM plant_events WHERE plant_id=:p", p=pid)

    ev = q("SELECT * FROM plant_events WHERE plant_id=:p", p=pid)
    if alerts and ev and ev[0]["first_visible_symptom"]:
        lead = (ev[0]["first_visible_symptom"] - alerts[0]).days
        st.metric("Lead time (days before visible symptom)", lead)

    t = df.set_index("photo_date")
    c1, c2 = st.columns(2)
    c1.subheader("Green area (%)"); c1.line_chart(t["green_area_pct"])
    c2.subheader("Greenness ratio"); c2.line_chart(t["greenness_ratio"])
    c1.subheader("Yellow pixels (%)"); c1.line_chart(t["yellow_pct"])
    c2.subheader("Stress prediction (1 = stress)"); c2.bar_chart(t["stress_pred"])
    st.subheader("Photos")
    cols = st.columns(5)
    for i, r in df.tail(10).iterrows():
        if os.path.exists(r["image_path"]):
            cols[i % 5].image(r["image_path"], caption=str(r["photo_date"]))
