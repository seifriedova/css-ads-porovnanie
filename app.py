"""
Minimum clicks a No conversion kampane — mesacny export novych eshopov a negative kw
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import json
import io
import base64
import requests
from datetime import date
from openpyxl import Workbook

KRAJINY = ["AT","BE","CH","CZ","DE","DK","ES","FI","FR","GR","HU","IE","IT","NL","NO","PL","PT","RO","SE","SK","UK","USA"]
USERS = ["Dan", "Kuba", "Káťa"]
FLAGS = {
    "AT":"🇦🇹","BE":"🇧🇪","CH":"🇨🇭","CZ":"🇨🇿","DE":"🇩🇪","DK":"🇩🇰",
    "ES":"🇪🇸","FI":"🇫🇮","FR":"🇫🇷","GR":"🇬🇷","HU":"🇭🇺","IE":"🇮🇪",
    "IT":"🇮🇹","NL":"🇳🇱","NO":"🇳🇴","PL":"🇵🇱","PT":"🇵🇹","RO":"🇷🇴",
    "SE":"🇸🇪","SK":"🇸🇰","UK":"🇬🇧","USA":"🇺🇸",
}
PASSWORD = "cssads2026"
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "")
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "seifriedova/css-ads-porovnanie")

st.set_page_config(page_title="CSS × Ads", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
  #MainMenu, footer { visibility: hidden; }
  [data-testid="collapsedControl"] { display: none; }
  .stApp { background: #f8fafc; }

  h1 { font-size: 22px !important; font-weight: 800 !important; color: #111 !important; line-height: 1.35 !important; }
  h2 { font-size: 18px !important; font-weight: 800 !important; color: #111 !important; }

  /* Upload karty */
  .ucard { border-radius: 18px; padding: 24px; margin-bottom: 4px; }
  .ucard-css { background: #f0fdf4; border: 2px solid #bbf7d0; }
  .ucard-ads { background: #eff6ff; border: 2px solid #bfdbfe; }
  .krok { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 8px; }
  .dot-g { display:inline-block; width:8px; height:8px; border-radius:50%; background:#16a34a; margin-right:6px; }
  .dot-b { display:inline-block; width:8px; height:8px; border-radius:50%; background:#2563eb; margin-right:6px; }
  .ctitle-g { font-size: 18px; font-weight: 800; color: #14532d; margin: 0 0 6px; }
  .ctitle-b { font-size: 18px; font-weight: 800; color: #1e3a8a; margin: 0 0 6px; }
  .cdesc { font-size: 13px; color: #555; line-height: 1.5; margin-bottom: 14px; }

  /* Výsledok */
  .res-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }
  .res-count { font-size: 32px; font-weight: 800; color: #16a34a; }
  .res-count small { font-size: 14px; font-weight: 500; color: #aaa; margin-left: 4px; }

  /* Karta na login/výber krajín */
  .mid-card {
    background: #fff; border-radius: 20px; padding: 44px 40px;
    box-shadow: 0 4px 32px rgba(0,0,0,0.06); border: 1px solid #f0f0f0;
  }
  .mid-brand { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1.5px; color: #bbb; margin-bottom: 20px; }

  .divider { border: none; border-top: 1px solid #f0f0f0; margin: 8px 0 28px; }

  /* Tlačidlá */
  .stButton > button { border-radius: 10px !important; font-weight: 600 !important; font-size: 14px !important; }
  .stButton > button[kind="primary"] { background: #111 !important; border: none !important; color: #fff !important; }
  .stButton > button[kind="primary"]:hover { background: #333 !important; }
  .red-btn .stButton > button { background: #dc2626 !important; color: #fff !important; border: none !important; }
  .red-btn .stButton > button:hover { background: #b91c1c !important; }

  [data-testid="stFileUploaderDropzone"] { border-radius: 12px !important; }

  /* Krajiny — radio štylizovaný ako taby */
  div[data-testid="stRadio"] > label { display: none !important; }
  div[data-testid="stRadio"] > div {
    display: flex !important; flex-wrap: wrap !important;
    gap: 6px !important; justify-content: flex-end !important;
  }
  div[data-testid="stRadio"] > div > label {
    min-width: 44px !important; padding: 5px 12px !important; border-radius: 8px !important;
    border: 1.5px solid #e5e5e5 !important; background: #fff !important;
    font-size: 12px !important; font-weight: 600 !important; color: #555 !important;
    cursor: pointer !important; text-align: center !important; justify-content: center !important;
  }
  div[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
  div[data-testid="stRadio"] > div > label:has(input:checked) {
    border-color: #16a34a !important; background: #16a34a !important; color: #fff !important;
  }
</style>
""", unsafe_allow_html=True)


# ── GITHUB FUNKCIE ────────────────────────────────────────────────────────────

def gh_load_history(country):
    if not GITHUB_TOKEN:
        return {}, None
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/historia_{country}.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return json.loads(content), data["sha"]
    except Exception:
        pass
    return {}, None


def gh_save_file(filename, content_bytes):
    """Uloží ľubovoľný súbor do GitHub repozitára."""
    if not GITHUB_TOKEN:
        return
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    # Získaj SHA ak súbor už existuje (pre update)
    sha = None
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            sha = r.json().get("sha")
    except Exception:
        pass
    content = base64.b64encode(content_bytes).decode("utf-8")
    payload = {"message": f"upload {filename}", "content": content}
    if sha:
        payload["sha"] = sha
    try:
        requests.put(url, headers=headers, json=payload, timeout=15)
    except Exception:
        pass


def gh_get_file(filename):
    """Stiahne raw obsah súboru z GitHubu. Vráti bytes alebo None."""
    if not GITHUB_TOKEN:
        return None
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            return base64.b64decode(r.json()["content"])
    except Exception:
        pass
    return None


def gh_save_history(country, history_data, sha=None):
    if not GITHUB_TOKEN:
        return False
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/historia_{country}.json"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    content = base64.b64encode(
        json.dumps(history_data, ensure_ascii=False, indent=2).encode("utf-8")
    ).decode("utf-8")
    payload = {"message": f"historia_{country} {date.today()}", "content": content}
    if sha:
        payload["sha"] = sha
    try:
        r = requests.put(url, headers=headers, json=payload, timeout=10)
        return r.status_code in (200, 201)
    except Exception:
        return False


# ── POMOCNÉ FUNKCIE ──────────────────────────────────────────────────────────

def generate_excel(shops_df):
    wb = Workbook()

    # List 1: Nové eshopy
    ws1 = wb.active
    ws1.title = "Nové eshopy"
    ws1.append(["Orig ID", "Eshop", "Štítok CSS"])
    for _, row in shops_df.iterrows():
        ws1.append([int(row["Orig ID"]), row["Název shopu"], row["Aktuální štítek"]])

    # List 2: Negative KW
    ws2 = wb.create_sheet("Negative KW")
    ws2.append(["Negative KW"])
    for _, row in shops_df.iterrows():
        domain = str(row["Název shopu"]).strip()
        ws2.append([f'"{domain}"'])
        without_tld = domain.rsplit(".", 1)[0]
        ws2.append([f'"{without_tld}"'])

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def extract_css_ids(df):
    col_status = "Aktuální štítek"
    col_id = "Orig ID"
    col_name = "Název shopu"
    col_manual = "Manuální štítky"
    valid = ["Minimum clicks", "No conversion"]
    mask = df[col_status].isin(valid)
    manual = df[col_manual].fillna("").str.strip().str.lower()
    excl = manual.isin(["css vypnuto", "css vypnuto_gmc"])
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


# ── 1. PRIHLÁSENIE ───────────────────────────────────────────────────────────

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.markdown("""
    <h1 style="text-align:center; margin: 48px 0 32px;">
      Minimum clicks a No conversion<br>mesačný update
    </h1>
    """, unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown('<div class="mid-brand" style="text-align:center">CSS × Ads</div>', unsafe_allow_html=True)
        pwd = st.text_input("Heslo", type="password", placeholder="Zadaj heslo...", label_visibility="collapsed")
        if st.button("Prihlásiť sa →", use_container_width=True, type="primary"):
            if pwd == PASSWORD:
                st.session_state.auth = True
                st.rerun()
            else:
                st.error("Nesprávne heslo.")
    st.stop()


# ── 2. VÝBER KRAJÍN ──────────────────────────────────────────────────────────

if "krajiny" not in st.session_state:
    st.session_state.krajiny = []

if not st.session_state.krajiny:
    _, col, _ = st.columns([1, 1.4, 1])
    with col:
        st.markdown('<div class="mid-brand">CSS × Ads</div>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:22px;font-weight:800;color:#111;margin-bottom:8px;">Pre ktoré krajiny budeš aktualizovať dáta?</p>', unsafe_allow_html=True)
        st.markdown('<p style="font-size:14px;color:#888;line-height:1.6;margin-bottom:28px;">Vyber krajiny ktoré spravuješ — appka ti zobrazí len ich.</p>', unsafe_allow_html=True)

        selected = []
        c1, c2, c3 = st.columns(3)
        cols_sel = [c1, c2, c3]
        for i, k in enumerate(KRAJINY):
            with cols_sel[i % 3]:
                if st.checkbox(f"**{k}**", key=f"sel_{k}"):
                    selected.append(k)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Pokračovať →", use_container_width=True, type="primary",
                     disabled=len(selected) == 0):
            st.session_state.krajiny = selected
            st.session_state.aktivna_krajina = selected[0]
            st.rerun()
    st.stop()


# ── 3. HLAVNÁ APPKA ─────────────────────────────────────────────────────────

if "aktivna_krajina" not in st.session_state:
    st.session_state.aktivna_krajina = st.session_state.krajiny[0]

krajina = st.session_state.aktivna_krajina

# Načítaj históriu z GitHubu (cached v session state)
hist_key = f"gh_hist_{krajina}"
sha_key = f"gh_sha_{krajina}"
if hist_key not in st.session_state:
    with st.spinner(f"Načítavam históriu {krajina}..."):
        h, sha = gh_load_history(krajina)
        st.session_state[hist_key] = h
        st.session_state[sha_key] = sha

history = st.session_state[hist_key]
history_sha = st.session_state[sha_key]
has_history = bool(history.get("ids"))

# ── Hlavička: nadpis + prepínač krajín ───────────────────────────────────────
hdr_left, hdr_right = st.columns([3, 2])

with hdr_left:
    st.markdown(f"""
    <h1>Minimum clicks a No conversion kampane —<br>mesačný export nových eshopov a negative kw</h1>
    <p style="font-size:13px;color:#aaa;margin-top:4px;margin-bottom:28px;">
      {FLAGS[krajina]} {krajina} · {date.today().strftime("%B %Y")}
    </p>
    """, unsafe_allow_html=True)

with hdr_right:
    if len(st.session_state.krajiny) > 1:
        nova = st.radio(
            "Krajina",
            st.session_state.krajiny,
            index=st.session_state.krajiny.index(krajina),
            horizontal=True,
            label_visibility="collapsed",
        )
        if nova != krajina:
            st.session_state.aktivna_krajina = nova
            st.rerun()
    else:
        k = st.session_state.krajiny[0]
        st.markdown(f'<div style="display:flex;justify-content:flex-end;padding-top:8px;"><span style="padding:5px 12px;border-radius:8px;border:1.5px solid #111;background:#111;color:#fff;font-size:12px;font-weight:700;">{k}</span></div>', unsafe_allow_html=True)

# ── Upload karty ─────────────────────────────────────────────────────────────
if has_history:
    st.markdown("""
    <div class="ucard ucard-css">
      <div class="krok"><span class="dot-g"></span>Krok 1 — CSS</div>
      <p class="ctitle-g">CSS export</p>
      <p class="cdesc">Mesačný export z CSS systému s tagmi Minimum clicks a No conversion.<br>Stĺpec <b>Orig ID</b> povinný.</p>
    </div>
    """, unsafe_allow_html=True)
    css_file = st.file_uploader("CSS súbor (CSV)", type="csv",
                                key=f"css_{krajina}", label_visibility="collapsed")
    ads_file = None
else:
    st.info("Prvý mesiac — nahraj aj Ads export. Od budúceho mesiaca stačí len CSS.")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        <div class="ucard ucard-css">
          <div class="krok"><span class="dot-g"></span>Krok 1 — CSS</div>
          <p class="ctitle-g">CSS export</p>
          <p class="cdesc">Mesačný export z CSS systému.<br>Stĺpec <b>Orig ID</b> povinný.</p>
        </div>
        """, unsafe_allow_html=True)
        css_file = st.file_uploader("CSS súbor (CSV)", type="csv",
                                    key=f"css_{krajina}", label_visibility="collapsed")
    with col2:
        st.markdown("""
        <div class="ucard ucard-ads">
          <div class="krok"><span class="dot-b"></span>Krok 2 — Ads</div>
          <p class="ctitle-b">Ads export</p>
          <p class="cdesc">Export skupín produktov z Google Ads.<br>Stĺpec <b>Custom label 4</b> obsahuje Orig ID.</p>
        </div>
        """, unsafe_allow_html=True)
        ads_file = st.file_uploader("Ads súbor (CSV)", type="csv",
                                    key=f"ads_{krajina}", label_visibility="collapsed")

if not css_file:
    st.stop()

# ── Spracovanie ───────────────────────────────────────────────────────────────
try:
    css_df = pd.read_csv(io.StringIO(css_file.read().decode("utf-8-sig", errors="replace")))
    css_shops = extract_css_ids(css_df)
    css_ids = set(css_shops["Orig ID"].astype(int))
    st.success(f"CSS: **{len(css_shops)}** eshopov (Minimum clicks + No conversion, bez CSS vypnuto)")
except KeyError as e:
    st.error(f"Stĺpec nenájdený v CSS súbore: {e}")
    st.stop()
except Exception as e:
    st.error(f"Chyba pri čítaní CSS: {e}")
    st.stop()

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

# ── Uložiť históriu do GitHubu ────────────────────────────────────────────────
st.markdown('<hr class="divider">', unsafe_allow_html=True)

mesiac = date.today().strftime("%Y-%m")
log = history.get("log", {})
log[mesiac] = {
    "nove_pridane": len(new_ids),
    "celkom_v_css": len(css_ids),
    "datum_nahrania": date.today().isoformat(),
}
updated_history = {
    "krajina": krajina,
    "ids": sorted(list(all_known_ids | css_ids)),
    "log": log,
}

btn_col1, btn_col2 = st.columns(2)
with btn_col1:
    st.download_button(
        label="⬇ Stiahnuť Excel (eshopy + negative KW)",
        data=generate_excel(new_shops),
        file_name=f"pridat_do_ads_{krajina}_{date.today()}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
        type="primary",
    )
with btn_col2:
    save_clicked = st.button("Uložiť históriu do GitHubu", use_container_width=True)
    st.markdown('<p style="font-size:12px;color:#888;margin-top:2px;">Nezabudni uložiť — bez toho budeš musieť budúci mesiac nahrať Ads export znova.</p>', unsafe_allow_html=True)

# JS — červený button pre "Uložiť históriu"
components.html("""
<script>
(function() {
  function styleBtn() {
    var buttons = window.parent.document.querySelectorAll('button');
    buttons.forEach(function(btn) {
      if (btn.innerText && btn.innerText.includes('Ulo\u017Ei\u0165 hist\u00F3riu do GitHubu')) {
        btn.style.setProperty('background', '#dc2626', 'important');
        btn.style.setProperty('color', '#fff', 'important');
        btn.style.setProperty('border', 'none', 'important');
      }
    });
  }
  styleBtn();
  setTimeout(styleBtn, 300);
  var obs = new MutationObserver(styleBtn);
  obs.observe(window.parent.document.body, {childList: true, subtree: true});
})();
</script>
""", height=0)

if save_clicked:
    with st.spinner("Ukladám..."):
        ok = gh_save_history(krajina, updated_history, history_sha)
        if ok:
            css_file.seek(0)
            gh_save_file(f"csv_{krajina}_{mesiac}.csv", css_file.read())
    if ok:
        st.session_state[hist_key] = updated_history
        st.session_state[sha_key] = None
        st.success(f"Hotovo! História {krajina} uložená. Budúci mesiac stačí nahrať len CSS CSV.")
    else:
        st.error("Nepodarilo sa uložiť na GitHub. Skontroluj GITHUB_TOKEN v Streamlit secrets.")

# ── História nahrania CSV ─────────────────────────────────────────────────────
if log:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown("#### História nahrania CSV")
    for m, v in sorted(log.items(), reverse=True):
        col_m, col_d, col_n, col_dl = st.columns([2, 2, 2, 2])
        col_m.markdown(f"**{m}**")
        col_d.write(v.get("datum_nahrania", "—"))
        col_n.write(f"{v.get('nove_pridane', '—')} nových eshopov")
        with col_dl:
            file_key = f"csv_file_{krajina}_{m}"
            if file_key not in st.session_state:
                st.session_state[file_key] = gh_get_file(f"csv_{krajina}_{m}.csv")
            if st.session_state[file_key]:
                st.download_button(
                    "⬇ CSV",
                    data=st.session_state[file_key],
                    file_name=f"css_{krajina}_{m}.csv",
                    mime="text/csv",
                    key=f"dl_{krajina}_{m}",
                )
            else:
                st.caption("nedostupné")
