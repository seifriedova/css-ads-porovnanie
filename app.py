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
NAMES = {"DE": "Nemecko", "FR": "Francúzsko", "SK": "Slovensko", "DK": "Dánsko", "CH": "Švajčiarsko"}
PASSWORD = "cssads2026"

st.set_page_config(page_title="CSS × Ads", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  #MainMenu, footer { visibility: hidden; }
  [data-testid="collapsedControl"] { display: none; }

  /* Celková stránka */
  .stApp { background: #f8fafc; }

  /* Nadpisy */
  h1 { font-size: 22px !important; font-weight: 800 !important; color: #111 !important; line-height: 1.35 !important; }
  h2 { font-size: 18px !important; font-weight: 800 !important; color: #111 !important; }
  h3 { font-size: 15px !important; font-weight: 700 !important; color: #333 !important; }

  /* Hlavička */
  .app-header {
    background: #fff;
    border-bottom: 1px solid #f0f0f0;
    padding: 16px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 32px;
    border-radius: 0;
  }
  .brand { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #bbb; }
  .ctabs { display: flex; gap: 6px; }
  .ctab {
    padding: 6px 14px; border-radius: 8px;
    border: 1.5px solid #e5e5e5; background: #fff;
    font-size: 13px; font-weight: 600; color: #555;
    display: inline-block;
  }
  .ctab.on { border-color: #111; background: #111; color: #fff; }

  /* Upload karty */
  .ucard {
    border-radius: 18px; padding: 24px;
    margin-bottom: 4px;
  }
  .ucard-css { background: #f0fdf4; border: 2px solid #bbf7d0; }
  .ucard-ads { background: #eff6ff; border: 2px solid #bfdbfe; }
  .krok { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 8px; }
  .dot-g { display:inline-block; width:8px; height:8px; border-radius:50%; background:#16a34a; margin-right:6px; }
  .dot-b { display:inline-block; width:8px; height:8px; border-radius:50%; background:#2563eb; margin-right:6px; }
  .ctitle-g { font-size: 18px; font-weight: 800; color: #14532d; margin: 0 0 6px; }
  .ctitle-b { font-size: 18px; font-weight: 800; color: #1e3a8a; margin: 0 0 6px; }
  .cdesc { font-size: 13px; color: #555; line-height: 1.5; margin-bottom: 14px; }

  /* Historia */
  .hist-bar {
    background: #fff; border: 1px solid #f0f0f0;
    border-radius: 12px; padding: 14px 20px;
    font-size: 13px; color: #888; margin: 12px 0 24px;
  }
  .hist-bar b { color: #555; }

  /* Výsledok */
  .res-header {
    display: flex; align-items: center;
    justify-content: space-between; margin-bottom: 16px;
  }
  .res-count { font-size: 32px; font-weight: 800; color: #16a34a; }
  .res-count small { font-size: 14px; font-weight: 500; color: #aaa; margin-left: 4px; }

  /* Prihlásenie / Setup karta */
  .mid-card {
    background: #fff; border-radius: 20px;
    padding: 44px 40px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.06);
    border: 1px solid #f0f0f0;
  }
  .mid-brand { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #bbb; margin-bottom: 20px; }
  .mid-title { font-size: 22px; font-weight: 800; color: #111; margin-bottom: 8px; }
  .mid-desc { font-size: 14px; color: #888; line-height: 1.6; margin-bottom: 28px; }

  /* Divider */
  .divider { border: none; border-top: 1px solid #f0f0f0; margin: 8px 0 28px; }

  /* Tlačidlá — štýlujeme Streamlit button */
  .stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
  }

  /* Skryť label nad file uploaderom ak je prázdny */
  [data-testid="stFileUploaderDropzone"] {
    border-radius: 12px !important;
  }
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
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="mid-card">', unsafe_allow_html=True)
        st.markdown('<div class="mid-brand">CSS × Ads</div>', unsafe_allow_html=True)
        st.markdown('<div class="mid-title">Prihlásenie</div>', unsafe_allow_html=True)
        st.markdown('<div class="mid-desc">Zadaj heslo pre prístup do appky.</div>', unsafe_allow_html=True)
        pwd = st.text_input("Heslo", type="password", placeholder="Zadaj heslo...", label_visibility="collapsed")
        if st.button("Prihlásiť sa →", use_container_width=True, type="primary"):
            if pwd == PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Nesprávne heslo.")
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# ── 2. VÝBER KRAJÍN ──────────────────────────────────────────────────────────

if "krajiny" not in st.session_state:
    st.session_state.krajiny = []

if not st.session_state.krajiny:
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div class="mid-card">', unsafe_allow_html=True)
        st.markdown('<div class="mid-brand">CSS × Ads</div>', unsafe_allow_html=True)
        st.markdown('<div class="mid-title">Pre ktoré krajiny budeš aktualizovať dáta?</div>', unsafe_allow_html=True)
        st.markdown('<div class="mid-desc">Vyber krajiny ktoré spravuješ — appka ti zobrazí len ich.</div>', unsafe_allow_html=True)

        selected = []
        c1, c2 = st.columns(2)
        for i, k in enumerate(KRAJINY):
            with (c1 if i % 2 == 0 else c2):
                if st.checkbox(f"{FLAGS[k]} **{k}** — {NAMES[k]}", key=f"sel_{k}"):
                    selected.append(k)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Pokračovať →", use_container_width=True, type="primary",
                     disabled=len(selected) == 0):
            st.session_state.krajiny = selected
            st.session_state.aktivna_krajina = selected[0]
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.stop()


# ── 3. HLAVNÁ APPKA ─────────────────────────────────────────────────────────

if "aktivna_krajina" not in st.session_state:
    st.session_state.aktivna_krajina = st.session_state.krajiny[0]

krajina = st.session_state.aktivna_krajina

# Hlavička s prepínačom krajín
tabs_html = "".join(
    f'<span class="ctab {"on" if k == krajina else ""}">{FLAGS[k]} {k}</span>'
    for k in st.session_state.krajiny
)
st.markdown(f"""
<div class="app-header">
  <div class="brand">CSS × Ads</div>
  <div class="ctabs">{tabs_html}</div>
</div>
""", unsafe_allow_html=True)

# Funkčný prepínač (radio skrytý pod hlavičkou)
if len(st.session_state.krajiny) > 1:
    nova = st.radio(
        "Krajina:",
        st.session_state.krajiny,
        index=st.session_state.krajiny.index(krajina),
        horizontal=True,
        format_func=lambda k: f"{FLAGS[k]} {k}",
    )
    if nova != krajina:
        st.session_state.aktivna_krajina = nova
        st.rerun()

# Nadpis
st.markdown(f"""
<h1>Minimum clicks a No conversion kampane —<br>mesačný export nových eshopov a negative kw</h1>
<p style="font-size:13px;color:#aaa;margin-top:4px;margin-bottom:28px;">
  Krajina {FLAGS[krajina]} {krajina} · {date.today().strftime("%B %Y")}
</p>
""", unsafe_allow_html=True)

# ── Upload karty ─────────────────────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    <div class="ucard ucard-css">
      <div class="krok"><span class="dot-g"></span>Krok 1 — CSS</div>
      <p class="ctitle-g">CSS export</p>
      <p class="cdesc">Mesačný export z CSS systému s tagmi Minimum clicks a No conversion.<br>Stĺpec <b>Orig ID</b> povinný.</p>
    </div>
    """, unsafe_allow_html=True)
    css_file = st.file_uploader("CSS súbor (CSV)", type="csv",
                                key=f"css_{krajina}", label_visibility="collapsed")

with col2:
    st.markdown("""
    <div class="ucard ucard-ads">
      <div class="krok"><span class="dot-b"></span>Krok 2 — Ads</div>
      <p class="ctitle-b">Ads export</p>
      <p class="cdesc">Export skupín produktov z Google Ads.<br>Stĺpec <b>Custom label 4</b> obsahuje Orig ID eshopov.</p>
    </div>
    """, unsafe_allow_html=True)
    ads_file = st.file_uploader("Ads súbor (CSV)", type="csv",
                                key=f"ads_{krajina}", label_visibility="collapsed")

# História
st.markdown(f"""
<div class="hist-bar">
  <b>História (od 2. mesiaca)</b> — nahraj <code>historia_{krajina}.json</code> namiesto Ads exportu
</div>
""", unsafe_allow_html=True)
hist_file = st.file_uploader(f"historia_{krajina}.json", type="json",
                              key=f"hist_{krajina}", label_visibility="collapsed")

if not css_file:
    st.info("Nahraj CSS súbor pre spustenie porovnania.")
    st.stop()

# ── Spracovanie ───────────────────────────────────────────────────────────────
try:
    css_df = pd.read_csv(io.StringIO(css_file.read().decode("utf-8-sig", errors="replace")))
    css_shops = extract_css_ids(css_df)
    css_ids = set(css_shops["Orig ID"].astype(int))
    st.success(f"CSS: **{len(css_shops)}** eshopov načítaných (Minimum clicks + No conversion, bez CSS vypnuto)")
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

# ── Výsledok ──────────────────────────────────────────────────────────────────
new_ids = css_ids - all_known_ids
new_shops = (css_shops[css_shops["Orig ID"].isin(new_ids)]
             .sort_values("Aktuální štítek")
             .reset_index(drop=True))

st.markdown('<hr class="divider">', unsafe_allow_html=True)

if new_shops.empty:
    st.success("Žiadne nové eshopy na pridanie tento mesiac!")
else:
    st.markdown(f"""
    <div class="res-header">
      <h2>Nové eshopy na pridanie do kampane {FLAGS[krajina]} {krajina}</h2>
      <div class="res-count">{len(new_shops)}<small>eshopov</small></div>
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

# ── História ──────────────────────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)
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
