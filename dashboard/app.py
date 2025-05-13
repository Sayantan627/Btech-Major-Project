# dashboard/app.py
import streamlit as st
import requests
import time

# ——— PAGE SETUP —————————————————————————————————————
st.set_page_config(page_title="Smart Parking Dashboard", layout="wide")
st.title("🚗 Smart Parking Lot Status")

# placeholder for grid
placeholder = st.empty()

API_URL = "http://localhost:8000/parking_status"

# ——— MAIN LOOP —————————————————————————————————————
while True:
    try:
        resp = requests.get(API_URL, timeout=1)
        data = resp.json()
    except Exception:
        st.error("⚠️ Could not fetch status from API.")
        time.sleep(2)
        continue

    slot_ids     = data["slot_ids"]
    statuses     = data["status"]
    last_changed = data["last_changed"]

    # draw grid: for simplicity, one row of columns
    cols = placeholder.columns(len(slot_ids))
    for col, sid, stt, ts in zip(cols, slot_ids, statuses, last_changed):
        color = "#90EE90" if stt=="free" else "#FF7F7F"
        # colored box + label
        col.markdown(
            f"""
            <div style="
              background:{color};
              border-radius:8px;
              height:100px;
              display:flex;
              align-items:center;
              justify-content:center;
              font-size:18px;
              font-weight:bold;">
                Slot {sid}
            </div>
            """,
            unsafe_allow_html=True
        )
        col.caption(f"Last change: {time.strftime('%H:%M:%S', time.localtime(ts))}")

    # summary
    free_count = statuses.count("free")
    occ_count  = statuses.count("occupied")
    st.sidebar.metric("Total slots", len(slot_ids))
    st.sidebar.metric("Free slots", free_count, delta=f"{free_count}/{len(slot_ids)}")
    st.sidebar.metric("Occupied", occ_count)

    time.sleep(1)  # refresh rate
