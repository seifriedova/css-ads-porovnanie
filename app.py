"""
CSS vs Ads porovnanie — mesacna rutina
Spustenie lokalne: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import json
import io
from datetime import date

KRAJINY = ["DE", "FR", "SK", "DK", "CH"]
PASSWORD = "cssads2026"   # <-- zmen si heslo podla seba


# ---------- autentifikacia ----------
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.title("CSS vs Ads — prihlasenie")
    pwd = st.text_input("Heslo", type="password")
    if st.button("Prihlasit sa"):
        if pwd == PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Nespravne heslo.")
    return False


# ---------- pomocne funkcie ----------
def extract_css_ids(df: pd.DataFrame) -> pd.DataFrame:
    col_status = "Aktuální štítek"
    col_id = "Orig ID"
    col_name = "Název shopu"
    col_manual = "Manuální štítky"

    valid_statuses = ["Minimum clicks", "No conversion"]
    mask_status = df[col_status].isin(valid_statuses)
    # Vylucit iba presne "CSS vypnuto" — "CSS vypnuto_GMC" ponechame
    mask_exclude = df[col_manual].fillna("").str.strip().str.lower() == "css vypnuto"
    result = df[mask_status & ~mask_exclude][[col_id, col_name, col_status, col_manual]].copy()
    result[col_id] = result[col_id].astype(int)
    return result


def extract_ads_ids(df: pd.DataFrame) -> set:
    col = "Skupina produktů"
    ids = set()
    for val in df[col].dropna():
        val = str(val)
        if "custom label 4" in val:
            try:
                part = val.split("custom label 4 =")[1]
                part = part.replace('"', "").replace("'", "").strip()
                if part.isdigit():
                    ids.add(int(part))
            except Exception:
                pass
    return ids


def load_history_from_file(uploaded_file) -> dict:
    if uploaded_file is None:
        return {}
    try:
        content = uploaded_file.read().decode("utf-8")
        return json.loads(content)
    except Exception:
        st.error("Chyba pri citani historia.json. Skontroluj subor.")
        return {}


# ---------- hlavna aplikacia ----------
if not check_password():
    st.stop()

st.set_page_config(page_title="CSS vs Ads", layout="wide")
st.title("CSS vs Ads — mesacna rutina")

# --- Vyber krajiny ---
krajina = st.sidebar.selectbox("Krajina", KRAJINY)
st.sidebar.divider()
st.sidebar.markdown("""
**Ako to funguje:**
1. Prvy mesiac: nahraj CSS + Ads subor
2. Stiahni aktualizovanu historiu (`.json`)
3. Dalsi mesiac: nahraj CSS + historia `.json`
4. Ads subor uz nie je potrebny
""")

st.subheader(f"Krajina: **{krajina}**")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("**CSS export** *(povinny)*")
    css_file = st.file_uploader("CSS subor", type="csv", key="css")

with col2:
    st.markdown("**Historia** *(z minuleho mesiaca)*")
    hist_file = st.file_uploader(f"historia_{krajina}.json", type="json", key="hist")

with col3:
    st.markdown("**Ads export** *(len prvy mesiac)*")
    ads_file = st.file_uploader("Ads subor (custom label 4)", type="csv", key="ads")

if not css_file:
    st.info("Nahraj CSS subor pre spustenie porovnania.")
    st.stop()

# --- Spracovanie CSS ---
try:
    css_raw = css_file.read().decode("utf-8-sig", errors="replace")
    css_df = pd.read_csv(io.StringIO(css_raw))
    css_shops = extract_css_ids(css_df)
    css_ids = set(css_shops["Orig ID"].astype(int))
    st.success(f"CSS: **{len(css_shops)}** eshopov (Minimum clicks + No conversion, bez CSS vypnuto)")
except KeyError as e:
    st.error(f"Stlpec nenajdeny v CSS subore: {e}")
    st.stop()
except Exception as e:
    st.error(f"Chyba pri citani CSS: {e}")
    st.stop()

# --- Nacitanie historie a Ads ---
history: dict = load_history_from_file(hist_file)
all_known_ids: set = set(history.get("ids", []))

if ads_file:
    try:
        ads_raw = ads_file.read().decode("utf-8-sig", errors="replace")
        ads_df = pd.read_csv(io.StringIO(ads_raw), skiprows=2)
        ads_ids = extract_ads_ids(ads_df)
        all_known_ids.update(ads_ids)
        st.success(f"Ads: **{len(ads_ids)}** ID nacitanych z kampane")
    except Exception as e:
        st.error(f"Chyba pri citani Ads suboru: {e}")
        st.stop()

# --- Porovnanie ---
new_ids = css_ids - all_known_ids
new_shops = css_shops[css_shops["Orig ID"].isin(new_ids)].copy()
new_shops = new_shops.sort_values("Aktuální štítek").reset_index(drop=True)

st.divider()

if new_shops.empty:
    st.success("Ziadne nove eshopy na pridanie tento mesiac!")
else:
    st.subheader(f"Na pridanie do kampane {krajina}: **{len(new_shops)} eshopov**")
    st.dataframe(
        new_shops.rename(columns={
            "Orig ID": "Orig ID",
            "Název shopu": "Eshop",
            "Aktuální štítek": "Stitok CSS",
            "Manuální štítky": "Manualny stitok",
        }),
        use_container_width=True,
        hide_index=True,
    )
    csv_out = new_shops.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Stiahnut zoznam CSV",
        data=csv_out,
        file_name=f"pridat_do_ads_{krajina}_{date.today()}.csv",
        mime="text/csv",
    )

# --- Aktualizacia a stiahnutie historie ---
st.divider()
st.subheader("Uzavriet mesiac a aktualizovat historiu")

mesiac = st.text_input(
    "Mesiac (pre zaznam)",
    value=date.today().strftime("%Y-%m"),
    help="Napr. 2026-03"
)

if st.button("Vygenerovat aktualizovanu historiu", type="primary"):
    # Zlucime staru historiu + vsetky aktualne CSS ID
    updated_ids = all_known_ids | css_ids
    history_log = history.get("log", {})
    history_log[mesiac] = {
        "nove_pridane": len(new_ids),
        "celkom_v_css": len(css_ids),
    }
    new_history = {
        "krajina": krajina,
        "ids": sorted(list(updated_ids)),
        "log": history_log,
    }
    hist_json = json.dumps(new_history, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button(
        label=f"Stiahnut historia_{krajina}.json",
        data=hist_json,
        file_name=f"historia_{krajina}.json",
        mime="application/json",
    )
    st.success(f"Historia obsahuje {len(updated_ids)} ID. Uloz tento subor — nahrajes ho pristu mesiac.")
