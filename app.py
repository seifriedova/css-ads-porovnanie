"""
Minimum clicks a No conversion kampane — mesacny export novych eshopov a negative kw
"""

import streamlit as st
import pandas as pd
import json
import io
from datetime import date

KRAJINY = ["DE", "FR", "SK", "DK", "CH"]
FLAGS = {"DE": "🇩🇪", "FR": "🇫🇷", "SK": "🇸🇰", "DK": "🇩🇰", "CH": "🇨🇭"}
PASSWORD = "cssads2026"

st.set_page_config(page_title="CSS × Ads", layout="wide", initial_sidebar_state="collapsed")

# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  #MainMenu, footer, header { visibility: hidden; }
  .block-container { padding: 0 !important; max-width: 100% !important; }

  .app-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 18px 48px; border-bottom: 1px solid #f0f0f0;
    background: #fff; position: sticky; top: 0; z-index: 100;
  }
  .app-header .brand {
    font-size: 13px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1.2px; color: #aaa;
  }
  .country-tabs { display: flex; gap: 6px; }
  .ctab {
    padding: 7px 16px; border-radius: 8px;
    border: 1.5px solid #e5e5e5; background: #fff;
    font-size: 13px; font-weight: 600; color: #555;
    display: inline-block;
  }
  .ctab.active { border-color: #111; background: #111; color: #fff; }

  .main-content { padding: 40px 48px; }

  .page-title { margin-bottom: 10px; }
  .page-title h1 {
    font-size: 21px; font-weight: 800;
    color: #111; line-height: 1.35; margin: 0 0 6px 0;
  }
  .page-subtitle { font-size: 13px; color: #aaa; margin: 0; }

  .upload-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 20px; margin: 28px 0 4px 0;
  }
  .upload-card { border-radius: 20px; padding: 28px 28px 16px; }
  .css-card { background: #f0fdf4; border: 2px solid #bbf7d0; }
  .ads-card { background: #eff6ff; border: 2px solid #bfdbfe; }

  .card-krok { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
  .dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
  .dot-green { background: #16a34a; }
  .dot-blue { background: #2563eb; }
  .krok-label {
    font-size: 11px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1px; color: #888;
  }
  .card-title-green { font-size: 19px; font-weight: 800; color: #14532d; margin: 0 0 8px; }
  .card-title-blue  { font-size: 19px; font-weight: 800; color: #1e3a8a; margin: 0 0 8px; }
  .card-desc { font-size: 13px; color: #555; line-height: 1.5; margin: 0; }

  .history-bar {
    background: #fafafa; border: 1px solid #efefef;
    border-radius: 12px; padding: 14px 22px;
    display: flex; align-items: center;
    justify-content: space-between; margin: 16px 0 28px 0;
  }
  .history-bar-text { font-size: 13px; color: #888; }
  .history-bar-text strong { color: #555; }

  .my-divider { border: none; border-top: 1px solid #f0f0f0; margin: 4px 0 28px; }

  .result-header {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 20px;
  }
  .result-header h2 { font-size: 18px; font-weight: 800; color: #111; margin: 0; }
  .result-count { font-size: 30px; font-weight: 800; color: #16a34a; }
  .result-count span { font-size: 13px; font-weight: 500; color: #888; margin-left: 4px; }

  .login-wrap {
    min-height: 100vh; display: flex;
    align-items: center; justify-content: center; background: #f8fafc;
  }
  .login-card {
    background: #fff; border-radius: 20px; padding: 48px; width: 400px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.07); border: 1px solid #f0f0f0;
  }
  .login-brand {
    font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.5px; color: #aaa; margin-bottom: 20px;
  }
  .login-title { font-size: 22px; font-weight: 800; margin-bottom: 28px; }

  .setup-wrap {
    min-height: 100vh; display: flex;
    align-items: center; justify-content: center; background: #f8fafc;
  }
  .setup-card {
    background: #fff; border-radius: 24px; padding: 52px 48px; width: 540px;
    box-shadow: 0 4px 40px rgba(0,0,0,0.07); border: 1px solid #f0f0f0;
  }
  .setup-brand {
    font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.5px; color: #aaa; margin-bottom: 24px;
  }
  .setup-title { font-size: 24px; font-weight: 800; margin-bottom: 10px; color: #111; }
  .setup-desc { font-size: 14px; color: #888; margin-bottom: 32px; line-height: 1.6; }
</style>
""", unsafe_allow_html=True)


# ── POMOCNÉ FUNKCIE ──────────────────────────────────────────────────────────

def extract_css_ids(df):
    col_status = "Aktuální štítek"
    col_id = "Orig ID"
    col_name = "Název shopu"
    col_manual = "Manuální štítky"
    valid = ["Minimum clicks", "No conversion"]
    mask = df[col_status].isin(valid)
    excl = df[col_manual].fillna("").str.strip().str.lower() == "css vypnuto"
    result = df[mask & ~excl][[col_id, col_name, col_status, col_manual]].copy()
    result[col_id] = result[col_id].astype(int)
    return result


def extract_ads_ids(df):
    ids = set()
    for val in df["Skupina produktů"].dropna():
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


def load_history(f):
    if f is None:
        return {}
    try:
        return json.loads(f.read().decode("utf-8"))
    except Exception:
        st.error("Chyba pri čítaní histórie. Skontroluj súbor.")
        return {}


# ── 1. PRIHLÁSENIE ───────────────────────────────────────────────────────────

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown('<div class="login-wrap"><div class="login-card">', unsafe_allow_html=True)
    st.markdown('<div class="login-brand">CSS × Ads</div>', unsafe_allow_html=True)
    st.markdown('<div class="login-title">Prihlásenie</div>', unsafe_allow_html=True)
    pwd = st.text_input("Heslo", type="password", label_visibility="collapsed",
                        placeholder="Zadaj heslo...")
    if st.button("Prihlásiť sa", use_container_width=True):
        if pwd == PASSWORD:
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("Nesprávne heslo.")
    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()


# ── 2. VÝBER KRAJÍN ──────────────────────────────────────────────────────────

if "krajiny" not in st.session_state:
    st.session_state.krajiny = []

if not st.session_state.krajiny:
    NAMES = {"DE": "Nemecko", "FR": "Francúzsko", "SK": "Slovensko", "DK": "Dánsko", "CH": "Švajčiarsko"}

    st.markdown('<div class="setup-wrap"><div class="setup-card">', unsafe_allow_html=True)
    st.markdown('<div class="setup-brand">CSS × Ads</div>', unsafe_allow_html=True)
    st.markdown('<div class="setup-title">Pre ktoré krajiny budeš aktualizovať dáta?</div>', unsafe_allow_html=True)
    st.markdown('<div class="setup-desc">Vyber krajiny ktoré spravuješ — appka ti zobrazí len ich.</div>', unsafe_allow_html=True)

    selected = []
    col_a, col_b = st.columns(2)
    for i, k in enumerate(KRAJINY):
        with (col_a if i % 2 == 0 else col_b):
            if st.checkbox(f"{FLAGS[k]}  **{k}** — {NAMES[k]}", key=f"sel_{k}"):
                selected.append(k)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Pokračovať →", use_container_width=True, disabled=len(selected) == 0):
        st.session_state.krajiny = selected
        st.session_state.aktivna_krajina = selected[0]
        st.rerun()

    st.markdown('</div></div>', unsafe_allow_html=True)
    st.stop()


# ── 3. HLAVNÁ APPKA ─────────────────────────────────────────────────────────

if "aktivna_krajina" not in st.session_state:
    st.session_state.aktivna_krajina = st.session_state.krajiny[0]

krajina = st.session_state.aktivna_krajina

# Hlavička
tabs_html = "".join(
    f'<span class="ctab {"active" if k == krajina else ""}">{FLAGS[k]} {k}</span>'
    for k in st.session_state.krajiny
)
st.markdown(f"""
<div class="app-header">
  <div class="brand">CSS × Ads</div>
  <div class="country-tabs">{tabs_html}</div>
</div>
""", unsafe_allow_html=True)

# Prepínač krajín (funkčný)
nova = st.radio("Prepnúť krajinu:", st.session_state.krajiny,
                index=st.session_state.krajiny.index(krajina),
                horizontal=True, label_visibility="collapsed")
if nova != krajina:
    st.session_state.aktivna_krajina = nova
    st.rerun()

st.markdown('<div class="main-content">', unsafe_allow_html=True)

# Nadpis
st.markdown(f"""
<div class="page-title">
  <h1>Minimum clicks a No conversion kampane —<br>mesačný export nových eshopov a negative kw</h1>
  <p class="page-subtitle">Krajina {FLAGS[krajina]} {krajina} · {date.today().strftime("%B %Y")}</p>
</div>
""", unsafe_allow_html=True)

# Upload karty
st.markdown("""
<div class="upload-grid">
  <div class="upload-card css-card">
    <div class="card-krok"><span class="dot dot-green"></span><span class="krok-label">Krok 1 — CSS</span></div>
    <p class="card-title-green">CSS export</p>
    <p class="card-desc">Mesačný export z CSS systému s tagmi Minimum clicks a No conversion. Stĺpec Orig ID povinný.</p>
  </div>
  <div class="upload-card ads-card">
    <div class="card-krok"><span class="dot dot-blue"></span><span class="krok-label">Krok 2 — Ads</span></div>
    <p class="card-title-blue">Ads export</p>
    <p class="card-desc">Export skupín produktov z Google Ads. Stĺpec Custom label 4 obsahuje Orig ID eshopov v kampani.</p>
  </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    css_file = st.file_uploader("CSS súbor", type="csv", key=f"css_{krajina}",
                                label_visibility="collapsed")
with col2:
    ads_file = st.file_uploader("Ads súbor", type="csv", key=f"ads_{krajina}",
                                label_visibility="collapsed")

# História
st.markdown(f"""
<div class="history-bar">
  <span class="history-bar-text"><strong>História (od 2. mesiaca)</strong> — nahraj historia_{krajina}.json namiesto Ads exportu</span>
</div>
""", unsafe_allow_html=True)
hist_file = st.file_uploader(f"historia_{krajina}.json", type="json",
                              key=f"hist_{krajina}", label_visibility="collapsed")

if not css_file:
    st.info("Nahraj CSS súbor pre spustenie porovnania.")
    st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# Spracovanie
try:
    css_df = pd.read_csv(io.StringIO(css_file.read().decode("utf-8-sig", errors="replace")))
    css_shops = extract_css_ids(css_df)
    css_ids = set(css_shops["Orig ID"].astype(int))
    st.success(f"CSS: **{len(css_shops)}** eshopov načítaných")
except KeyError as e:
    st.error(f"Stĺpec nenájdený v CSS súbore: {e}")
    st.stop()
except Exception as e:
    st.error(f"Chyba pri čítaní CSS: {e}")
    st.stop()

history = load_history(hist_file)
all_known_ids = set(history.get("ids", []))

if ads_file:
    try:
        ads_df = pd.read_csv(io.StringIO(ads_file.read().decode("utf-8-sig", errors="replace")), skiprows=2)
        ads_ids = extract_ads_ids(ads_df)
        all_known_ids.update(ads_ids)
        st.success(f"Ads: **{len(ads_ids)}** ID načítaných z kampane")
    except Exception as e:
        st.error(f"Chyba pri čítaní Ads súboru: {e}")
        st.stop()

# Výsledok
new_ids = css_ids - all_known_ids
new_shops = css_shops[css_shops["Orig ID"].isin(new_ids)].sort_values("Aktuální štítek").reset_index(drop=True)

st.markdown('<hr class="my-divider">', unsafe_allow_html=True)

if new_shops.empty:
    st.success("Žiadne nové eshopy na pridanie tento mesiac!")
else:
    st.markdown(f"""
    <div class="result-header">
      <h2>Nové eshopy na pridanie do kampane {FLAGS[krajina]} {krajina}</h2>
      <div class="result-count">{len(new_shops)}<span>eshopov</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.dataframe(
        new_shops.rename(columns={
            "Orig ID": "Orig ID",
            "Název shopu": "Eshop",
            "Aktuální štítek": "Štítok CSS",
            "Manuální štítky": "Manuálny štítok",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        label="⬇ Stiahnuť zoznam CSV",
        data=new_shops.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"pridat_do_ads_{krajina}_{date.today()}.csv",
        mime="text/csv",
    )

# História
st.markdown('<hr class="my-divider">', unsafe_allow_html=True)
st.subheader("Uložiť históriu")
mesiac = st.text_input("Mesiac", value=date.today().strftime("%Y-%m"), help="Napr. 2026-03")

if st.button("Vygenerovať aktualizovanú históriu", type="primary"):
    updated_ids = all_known_ids | css_ids
    log = history.get("log", {})
    log[mesiac] = {"nove_pridane": len(new_ids), "celkom_v_css": len(css_ids)}
    new_history = {"krajina": krajina, "ids": sorted(list(updated_ids)), "log": log}
    st.download_button(
        label=f"⬇ Stiahnuť historia_{krajina}.json",
        data=json.dumps(new_history, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name=f"historia_{krajina}.json",
        mime="application/json",
    )
    st.success(f"Hotovo! História obsahuje {len(updated_ids)} ID. Ulož súbor — nahráš ho budúci mesiac.")

st.markdown('</div>', unsafe_allow_html=True)
