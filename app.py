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


def zeige_formular(repo):
    """Zeigt das Rechnungsformular und verarbeitet die Erstellung."""
    st.title("BALANCE Vital-Lounge")
    st.subheader("Rechnung erstellen")
    st.divider()

    kunde = st.session_state.ausgewaehlter_kunde

    # ── Vorausfüllen je nach Modus ──
    if st.session_state.empfaenger_modus == "neu":
        vorbelegung_name = ""
        vorbelegung_adr1 = ""
        vorbelegung_adr2 = ""
        vorbelegung_leistung = ""
    else:
        vorbelegung_name = kunde.get("name", "")
        adr = kunde.get("adresse", ["", ""])
        vorbelegung_adr1 = adr[0] if len(adr) > 0 else ""
        vorbelegung_adr2 = adr[1] if len(adr) > 1 else ""
        vorbelegung_leistung = ""  # wird unten gesetzt

    # ── Leistungstext-Bestätigung bei bestehendem Kunden ──
    if st.session_state.empfaenger_modus == "bestehend" and st.session_state.leistung_bestaetigt is None:
        letzte = kunde.get("letzte_leistung", "")
        if letzte:
            st.info(f"**Letzter Rechnungstext:**\n\n_{letzte}_")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Ja, gleicher Text"):
                    st.session_state.leistung_bestaetigt = True
                    st.rerun()
            with col2:
                if st.button("✏️ Nein, neu schreiben"):
                    st.session_state.leistung_bestaetigt = False
                    st.rerun()
            return
        else:
            st.session_state.leistung_bestaetigt = False

    # Leistungstext festlegen
    if st.session_state.empfaenger_modus == "bestehend" and st.session_state.leistung_bestaetigt:
        vorbelegung_leistung = kunde.get("letzte_leistung", "")
    else:
        vorbelegung_leistung = ""

    # ── Formularfelder ──
    name = st.text_input("Empfängername *", value=vorbelegung_name)
    adr1 = st.text_input("Adresszeile 1 *", value=vorbelegung_adr1)
    adr2 = st.text_input("Adresszeile 2 *", value=vorbelegung_adr2)
    leistung = st.text_area("Leistungsbeschreibung *", value=vorbelegung_leistung, height=100)
    betrag = st.number_input("Betrag (€) *", min_value=0.01, step=0.01, format="%.2f")
    modus = st.radio("Betrag ist:", ["Netto (+ 19% MwSt)", "Brutto (inkl. MwSt)"])

    st.divider()

    col_zurueck, col_erstellen = st.columns([1, 2])
    with col_zurueck:
        if st.button("← Zurück"):
            st.session_state.empfaenger_modus = None
            st.session_state.ausgewaehlter_kunde = None
            st.session_state.leistung_bestaetigt = None
            st.rerun()

    with col_erstellen:
        if st.button("🧾 Rechnung erstellen", type="primary", use_container_width=True):
            # Pflichtfelder prüfen
            if not all([name, adr1, adr2, leistung, betrag]):
                st.error("Bitte alle Felder ausfüllen.")
                return

            ist_brutto = "Brutto" in modus

            # MwSt berechnen
            if ist_brutto:
                brutto = betrag
                netto = round(brutto / 1.19, 2)
                mwst_betrag = round(brutto - netto, 2)
            else:
                netto = betrag
                mwst_betrag = round(netto * 0.19, 2)
                brutto = round(netto + mwst_betrag, 2)

            with st.spinner("Rechnung wird erstellt..."):
                try:
                    # Rechnungsnummer aus GitHub lesen
                    rechnungsnummer = lese_naechste_nummer(repo)

                    # PDF erstellen
                    pdf_bytes = erstelle_pdf_bytes(
                        empfaenger_name=name,
                        empfaenger_adresse=[adr1, adr2],
                        leistung=leistung,
                        netto=netto,
                        mwst_betrag=mwst_betrag,
                        brutto=brutto,
                        rechnungsnummer=rechnungsnummer,
                        rechnungsdatum=date.today(),
                    )

                    # Counter in GitHub speichern
                    schreibe_counter(repo, rechnungsnummer)

                    # Kundendaten speichern/aktualisieren
                    speichere_kunde(repo, name, [adr1, adr2], leistung)

                    # E-Mail verschicken
                    sende_rechnung(
                        pdf_bytes=pdf_bytes,
                        rechnungsnummer=rechnungsnummer,
                        empfaenger_name=name,
                        gmail_absender=st.secrets["GMAIL_ABSENDER"],
                        gmail_passwort=st.secrets["GMAIL_APP_PASSWORT"],
                    )

                    st.success(
                        f"✅ Rechnung **{rechnungsnummer}** wurde erfolgreich an "
                        f"umohr@balance-sonnenstudio.de geschickt."
                    )

                    # Session zurücksetzen für nächste Rechnung
                    st.session_state.empfaenger_modus = None
                    st.session_state.ausgewaehlter_kunde = None
                    st.session_state.leistung_bestaetigt = None

                except Exception as e:
                    st.error(f"Fehler: {e}")


# ── Haupt-Routing ──
if not st.session_state.eingeloggt:
    zeige_login()
elif st.session_state.empfaenger_modus is None:
    zeige_empfaenger_auswahl()
elif st.session_state.empfaenger_modus == "bestehend" and st.session_state.ausgewaehlter_kunde is None:
    repo = verbinde_repo(st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"])
    zeige_kunden_auswahl(repo)
else:
    repo = verbinde_repo(st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"])
    zeige_formular(repo)
