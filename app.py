# Streamlit-Web-App: Rechnungserstellung für BALANCE Vital-Lounge
import streamlit as st
from datetime import date
from github_service import verbinde_repo, lese_naechste_nummer, schreibe_counter, lese_kunden, speichere_kunde
from email_service import sende_rechnung
from rechnung_erstellen import erstelle_pdf_bytes

# ── Seitenkonfiguration ──
st.set_page_config(
    page_title="BALANCE – Rechnung erstellen",
    page_icon="🧾",
    layout="centered",
)

# ── Session-State initialisieren ──
if "eingeloggt" not in st.session_state:
    st.session_state.eingeloggt = False
if "empfaenger_modus" not in st.session_state:
    st.session_state.empfaenger_modus = None  # "neu" oder "bestehend"
if "ausgewaehlter_kunde" not in st.session_state:
    st.session_state.ausgewaehlter_kunde = None
if "leistung_bestaetigt" not in st.session_state:
    st.session_state.leistung_bestaetigt = None  # True/False/None


def zeige_login():
    """Zeigt das Passwortfeld an."""
    st.title("BALANCE Vital-Lounge")
    st.subheader("Rechnung erstellen")
    st.divider()
    passwort = st.text_input("Bitte Passwort eingeben:", type="password")
    if st.button("Anmelden"):
        if passwort == st.secrets["APP_PASSWORT"]:
            st.session_state.eingeloggt = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")


def zeige_empfaenger_auswahl():
    """Zeigt die zwei Schaltflächen: Neuer oder Bestehender Empfänger."""
    st.title("BALANCE Vital-Lounge")
    st.subheader("Für wen soll die Rechnung ausgestellt werden?")
    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Neuer Rechnungsempfänger", use_container_width=True):
            st.session_state.empfaenger_modus = "neu"
            st.rerun()
    with col2:
        if st.button("📋 Bestehender Rechnungsempfänger", use_container_width=True):
            st.session_state.empfaenger_modus = "bestehend"
            st.rerun()


def zeige_kunden_auswahl(repo):
    """Zeigt die Liste der bestehenden Kunden zur Auswahl."""
    st.subheader("Kunden auswählen")
    kunden = lese_kunden(repo)

    if not kunden:
        st.warning("Noch keine Kunden gespeichert. Bitte 'Neuer Rechnungsempfänger' wählen.")
        if st.button("← Zurück"):
            st.session_state.empfaenger_modus = None
            st.rerun()
        return

    namen = [k["name"] for k in kunden]
    auswahl = st.selectbox("Kunde:", namen)
    ausgewaehlter = next(k for k in kunden if k["name"] == auswahl)

    if st.button("Weiter →"):
        st.session_state.ausgewaehlter_kunde = ausgewaehlter
        st.session_state.leistung_bestaetigt = None
        st.rerun()


# ── Haupt-Routing ──
if not st.session_state.eingeloggt:
    zeige_login()
elif st.session_state.empfaenger_modus is None:
    zeige_empfaenger_auswahl()
elif st.session_state.empfaenger_modus == "bestehend" and st.session_state.ausgewaehlter_kunde is None:
    repo = verbinde_repo(st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"])
    zeige_kunden_auswahl(repo)
else:
    # Formular wird in Task 6 ergänzt
    st.info("Formular folgt in Task 6...")
