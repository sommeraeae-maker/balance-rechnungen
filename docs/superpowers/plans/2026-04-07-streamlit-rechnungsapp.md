# Streamlit Rechnungs-Web-App – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eine passwortgeschützte Streamlit-Web-App die Rechnungen erstellt, per GitHub den Zähler und Kundendaten speichert, und die fertige PDF per Gmail verschickt.

**Architecture:** Die App besteht aus drei Hilfsdateien (`github_service.py`, `email_service.py`, erweitertes `rechnung_erstellen.py`) plus einer `app.py` als Streamlit-Oberfläche. Alle Zugangsdaten liegen in Streamlit Secrets. Der Rechnungszähler und Kundendaten werden direkt im GitHub-Repo gespeichert.

**Tech Stack:** Python 3, Streamlit, PyGithub, reportlab, pypdf, smtplib (eingebaut)

---

## Dateiübersicht

| Datei | Aktion | Zweck |
|---|---|---|
| `rechnung_erstellen.py` | Erweitern | Neue Funktion `erstelle_pdf_bytes()` ohne Seiteneffekte |
| `github_service.py` | Neu erstellen | Zähler und Kundendaten via GitHub API lesen/schreiben |
| `email_service.py` | Neu erstellen | PDF per Gmail verschicken |
| `app.py` | Neu erstellen | Streamlit-Oberfläche (Login, Kundenauswahl, Formular) |
| `requirements.txt` | Neu erstellen | Abhängigkeiten für Streamlit Cloud |
| `.gitignore` | Neu erstellen | Fertige Rechnungen und Secrets ausschließen |
| `tests/test_github_service.py` | Neu erstellen | Tests für GitHub-Hilfsfunktionen |
| `tests/test_email_service.py` | Neu erstellen | Tests für E-Mail-Versand |
| `tests/test_rechnung_bytes.py` | Neu erstellen | Tests für `erstelle_pdf_bytes()` |

---

## Task 1: `erstelle_pdf_bytes()` in rechnung_erstellen.py ergänzen

**Files:**
- Modify: `rechnung_erstellen.py`
- Test: `tests/test_rechnung_bytes.py`

Diese neue Funktion nimmt alle Parameter direkt entgegen (inkl. Rechnungsnummer) und gibt PDF-Bytes zurück. Keine Datei wird geschrieben, kein Zähler wird verändert. Die bestehende `erstelle_rechnung()` bleibt unverändert.

- [ ] **Schritt 1: Testdatei anlegen**

Erstelle `tests/test_rechnung_bytes.py` mit folgendem Inhalt:

```python
# Tests für die seiteneffektfreie PDF-Erstellungsfunktion
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from rechnung_erstellen import erstelle_pdf_bytes

def test_erstelle_pdf_bytes_gibt_bytes_zurueck():
    """Funktion muss bytes-Objekt zurückgeben"""
    result = erstelle_pdf_bytes(
        empfaenger_name="Test GmbH",
        empfaenger_adresse=["Musterstr. 1", "12345 Berlin"],
        leistung="Testleistung",
        netto=100.0,
        mwst_betrag=19.0,
        brutto=119.0,
        rechnungsnummer="RE-2026-999",
        rechnungsdatum=date(2026, 4, 7),
    )
    assert isinstance(result, bytes)
    assert len(result) > 1000  # echte PDF ist groesser als 1kb

def test_erstelle_pdf_bytes_enthaelt_pdf_header():
    """Ergebnis muss eine gueltige PDF sein"""
    result = erstelle_pdf_bytes(
        empfaenger_name="Test GmbH",
        empfaenger_adresse=["Musterstr. 1", "12345 Berlin"],
        leistung="Testleistung",
        netto=100.0,
        mwst_betrag=19.0,
        brutto=119.0,
        rechnungsnummer="RE-2026-999",
        rechnungsdatum=date(2026, 4, 7),
    )
    assert result[:4] == b"%PDF"
```

- [ ] **Schritt 2: Test ausführen – muss FEHLSCHLAGEN**

```bash
cd "/Users/marcelsommer/Desktop/Rechnung auf Knopf druck "
python -m pytest tests/test_rechnung_bytes.py -v
```

Erwartetes Ergebnis: `ImportError: cannot import name 'erstelle_pdf_bytes'`

- [ ] **Schritt 3: `erstelle_pdf_bytes()` zu rechnung_erstellen.py hinzufügen**

Füge direkt nach der Funktion `erstelle_rechnungsebene()` (nach Zeile 201) diese neue Funktion ein:

```python
def erstelle_pdf_bytes(
    empfaenger_name: str,
    empfaenger_adresse: list[str],
    leistung: str,
    netto: float,
    mwst_betrag: float,
    brutto: float,
    rechnungsnummer: str,
    rechnungsdatum,
) -> bytes:
    """Erstellt die fertige Rechnung als PDF-Bytes.
    Keine Seiteneffekte: kein Zähler, keine Datei wird geschrieben.
    Wird von der Streamlit-Web-App verwendet."""

    # Rechnungsebene erstellen
    ebene_bytes = erstelle_rechnungsebene(
        empfaenger_name=empfaenger_name,
        empfaenger_adresse=empfaenger_adresse,
        leistung=leistung,
        netto=netto,
        mwst_betrag=mwst_betrag,
        brutto=brutto,
        rechnungsnummer=rechnungsnummer,
        rechnungsdatum=rechnungsdatum,
    )

    # Briefbogen laden und zusammenführen
    briefbogen = PdfReader(TEMPLATE_PDF)
    seite = briefbogen.pages[0]
    ebene_pdf = PdfReader(BytesIO(ebene_bytes))
    seite.merge_page(ebene_pdf.pages[0])

    # Als Bytes zurückgeben
    writer = PdfWriter()
    writer.add_page(seite)
    puffer = BytesIO()
    writer.write(puffer)
    return puffer.getvalue()
```

- [ ] **Schritt 4: Test ausführen – muss BESTEHEN**

```bash
python -m pytest tests/test_rechnung_bytes.py -v
```

Erwartetes Ergebnis: `2 passed`

- [ ] **Schritt 5: Commit**

```bash
cd "/Users/marcelsommer/Desktop/Rechnung auf Knopf druck "
git add rechnung_erstellen.py tests/test_rechnung_bytes.py
git commit -m "feat: erstelle_pdf_bytes() fuer seiteneffektfreie PDF-Erstellung"
```

---

## Task 2: github_service.py erstellen

**Files:**
- Create: `github_service.py`
- Test: `tests/test_github_service.py`

Alle GitHub-Zugriffe (Zähler lesen/schreiben, Kunden lesen/schreiben) sind hier zentralisiert.

- [ ] **Schritt 1: Testdatei anlegen**

Erstelle `tests/test_github_service.py`:

```python
# Tests fuer den GitHub-Dienst (mit gemocktem PyGithub)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json, base64
from unittest.mock import MagicMock, patch
from datetime import date

import github_service


def _mock_repo(counter_inhalt: dict, kunden_dateien: list[dict]) -> MagicMock:
    """Hilfsfunktion: erstellt einen gefälschten GitHub-Repo-Mock"""
    repo = MagicMock()

    # counter.json Mock
    counter_datei = MagicMock()
    counter_datei.decoded_content = json.dumps(counter_inhalt).encode()
    counter_datei.sha = "abc123"

    # Kunden/ Verzeichnis Mock
    kunden_mocks = []
    for k in kunden_dateien:
        f = MagicMock()
        f.name = k["dateiname"]
        f.decoded_content = json.dumps(k["inhalt"]).encode()
        kunden_mocks.append(f)

    def get_contents(pfad):
        if pfad == "counter.json":
            return counter_datei
        if pfad == "Kunden":
            return kunden_mocks
        for k in kunden_mocks:
            if pfad == f"Kunden/{k.name}":
                return k
        raise Exception(f"Nicht gefunden: {pfad}")

    repo.get_contents.side_effect = get_contents
    return repo


def test_lese_counter_aktuelles_jahr():
    """Zähler des aktuellen Jahres wird korrekt gelesen"""
    aktuelles_jahr = date.today().year
    repo = _mock_repo({"letzteNummer": 5, "jahr": aktuelles_jahr}, [])
    nummer = github_service.lese_naechste_nummer(repo)
    assert nummer == f"RE-{aktuelles_jahr}-006"


def test_lese_counter_jahreswechsel():
    """Bei Jahreswechsel startet Zähler bei 001"""
    repo = _mock_repo({"letzteNummer": 99, "jahr": 2025}, [])
    aktuelles_jahr = date.today().year
    nummer = github_service.lese_naechste_nummer(repo)
    assert nummer == f"RE-{aktuelles_jahr}-001"


def test_lese_kunden_gibt_liste_zurueck():
    """Alle Kunden-JSONs werden als Liste zurückgegeben"""
    repo = _mock_repo(
        {"letzteNummer": 1, "jahr": 2026},
        [
            {"dateiname": "Firma_A.json", "inhalt": {"name": "Firma A", "adresse": ["Str. 1", "10000 Berlin"], "letzte_leistung": "Leistung X"}},
            {"dateiname": "Firma_B.json", "inhalt": {"name": "Firma B", "adresse": ["Str. 2", "20000 Hamburg"], "letzte_leistung": "Leistung Y"}},
        ]
    )
    kunden = github_service.lese_kunden(repo)
    assert len(kunden) == 2
    assert kunden[0]["name"] == "Firma A"
    assert kunden[1]["name"] == "Firma B"
```

- [ ] **Schritt 2: Test ausführen – muss FEHLSCHLAGEN**

```bash
python -m pytest tests/test_github_service.py -v
```

Erwartetes Ergebnis: `ModuleNotFoundError: No module named 'github_service'`

- [ ] **Schritt 3: github_service.py erstellen**

Erstelle `github_service.py`:

```python
# GitHub-Dienst: Zähler und Kundendaten aus dem GitHub-Repo lesen und schreiben
import json
import base64
from datetime import date


def verbinde_repo(github_token: str, repo_name: str):
    """Gibt ein verbundenes PyGithub-Repo-Objekt zurück."""
    from github import Github
    g = Github(github_token)
    return g.get_repo(repo_name)


def lese_naechste_nummer(repo) -> str:
    """Liest counter.json aus GitHub und gibt die NÄCHSTE Rechnungsnummer zurück.
    Schreibt noch NICHT zurück – das passiert erst nach erfolgreicher Erstellung."""
    datei = repo.get_contents("counter.json")
    daten = json.loads(datei.decoded_content)

    aktuelles_jahr = date.today().year
    if daten.get("jahr") != aktuelles_jahr:
        daten["letzteNummer"] = 0
        daten["jahr"] = aktuelles_jahr

    naechste = daten["letzteNummer"] + 1
    return f"RE-{aktuelles_jahr}-{naechste:03d}"


def schreibe_counter(repo, rechnungsnummer: str):
    """Schreibt die verwendete Rechnungsnummer als neue letzteNummer zurück nach GitHub."""
    # Nummer aus String extrahieren: RE-2026-009 → 9
    teile = rechnungsnummer.split("-")
    jahr = int(teile[1])
    nummer = int(teile[2])

    neue_daten = {"letzteNummer": nummer, "jahr": jahr}
    datei = repo.get_contents("counter.json")
    repo.update_file(
        path="counter.json",
        message=f"Rechnungsnummer {rechnungsnummer} vergeben",
        content=json.dumps(neue_daten, indent=2, ensure_ascii=False),
        sha=datei.sha,
    )


def lese_kunden(repo) -> list[dict]:
    """Liest alle Kunden-JSON-Dateien aus Kunden/ und gibt sie als Liste zurück."""
    try:
        dateien = repo.get_contents("Kunden")
    except Exception:
        return []

    kunden = []
    for datei in dateien:
        if datei.name.endswith(".json"):
            inhalt = json.loads(datei.decoded_content)
            inhalt["_dateiname"] = datei.name  # intern merken für späteres Schreiben
            kunden.append(inhalt)

    return sorted(kunden, key=lambda k: k.get("name", ""))


def speichere_kunde(repo, name: str, adresse: list[str], letzte_leistung: str):
    """Legt einen neuen Kunden an oder aktualisiert den bestehenden in Kunden/."""
    # Dateiname aus Kundennamen ableiten
    sicherer_name = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
    pfad = f"Kunden/{sicherer_name}.json"

    inhalt = {
        "name": name,
        "adresse": adresse,
        "letzte_leistung": letzte_leistung,
    }
    inhalt_str = json.dumps(inhalt, indent=2, ensure_ascii=False)

    # Prüfen ob Datei bereits existiert (Update vs. Create)
    try:
        bestehend = repo.get_contents(pfad)
        repo.update_file(
            path=pfad,
            message=f"Kundendaten aktualisiert: {name}",
            content=inhalt_str,
            sha=bestehend.sha,
        )
    except Exception:
        repo.create_file(
            path=pfad,
            message=f"Neuer Kunde angelegt: {name}",
            content=inhalt_str,
        )
```

- [ ] **Schritt 4: Tests ausführen – müssen BESTEHEN**

```bash
python -m pytest tests/test_github_service.py -v
```

Erwartetes Ergebnis: `3 passed`

- [ ] **Schritt 5: Commit**

```bash
git add github_service.py tests/test_github_service.py
git commit -m "feat: GitHub-Dienst fuer Zaehler und Kundenverwaltung"
```

---

## Task 3: email_service.py erstellen

**Files:**
- Create: `email_service.py`
- Test: `tests/test_email_service.py`

- [ ] **Schritt 1: Testdatei anlegen**

Erstelle `tests/test_email_service.py`:

```python
# Tests fuer den E-Mail-Dienst (smtplib wird gemockt)
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import patch, MagicMock
import email_service


def test_sende_rechnung_baut_korrekte_mail():
    """Prüft dass die E-Mail korrekt aufgebaut und abgeschickt wird"""
    fake_pdf = b"%PDF-1.4 fake content"

    with patch("smtplib.SMTP_SSL") as mock_smtp_klasse:
        mock_smtp = MagicMock()
        mock_smtp_klasse.return_value.__enter__ = MagicMock(return_value=mock_smtp)
        mock_smtp_klasse.return_value.__exit__ = MagicMock(return_value=False)

        email_service.sende_rechnung(
            pdf_bytes=fake_pdf,
            rechnungsnummer="RE-2026-009",
            empfaenger_name="Test GmbH",
            gmail_absender="test@gmail.com",
            gmail_passwort="geheim",
        )

        # sendmail muss aufgerufen worden sein
        assert mock_smtp.sendmail.called
        args = mock_smtp.sendmail.call_args
        absender = args[0][0]
        empfaenger = args[0][1]
        assert absender == "test@gmail.com"
        assert empfaenger == "umohr@balance-sonnenstudio.de"
```

- [ ] **Schritt 2: Test ausführen – muss FEHLSCHLAGEN**

```bash
python -m pytest tests/test_email_service.py -v
```

Erwartetes Ergebnis: `ModuleNotFoundError: No module named 'email_service'`

- [ ] **Schritt 3: email_service.py erstellen**

Erstelle `email_service.py`:

```python
# E-Mail-Dienst: fertige Rechnung als PDF per Gmail verschicken
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# Fester Empfänger
EMPFAENGER = "umohr@balance-sonnenstudio.de"


def sende_rechnung(
    pdf_bytes: bytes,
    rechnungsnummer: str,
    empfaenger_name: str,
    gmail_absender: str,
    gmail_passwort: str,
):
    """Verschickt die Rechnung als PDF-Anhang per Gmail."""
    nachricht = MIMEMultipart()
    nachricht["From"] = gmail_absender
    nachricht["To"] = EMPFAENGER
    nachricht["Subject"] = f"Rechnung {rechnungsnummer} – BALANCE Vital-Lounge"

    # E-Mail-Text
    text = (
        f"Hallo,\n\n"
        f"anbei die Rechnung {rechnungsnummer} für {empfaenger_name}.\n\n"
        f"Viele Grüße\nBALANCE Vital-Lounge"
    )
    nachricht.attach(MIMEText(text, "plain", "utf-8"))

    # PDF als Anhang
    anhang = MIMEBase("application", "octet-stream")
    anhang.set_payload(pdf_bytes)
    encoders.encode_base64(anhang)
    anhang.add_header(
        "Content-Disposition",
        f"attachment; filename={rechnungsnummer}_{empfaenger_name.replace(' ', '_')}.pdf",
    )
    nachricht.attach(anhang)

    # Versenden über Gmail SMTP
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(gmail_absender, gmail_passwort)
        server.sendmail(gmail_absender, EMPFAENGER, nachricht.as_string())
```

- [ ] **Schritt 4: Tests ausführen – müssen BESTEHEN**

```bash
python -m pytest tests/test_email_service.py -v
```

Erwartetes Ergebnis: `1 passed`

- [ ] **Schritt 5: Commit**

```bash
git add email_service.py tests/test_email_service.py
git commit -m "feat: E-Mail-Dienst fuer PDF-Versand per Gmail"
```

---

## Task 4: requirements.txt und .gitignore anlegen

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`

- [ ] **Schritt 1: requirements.txt erstellen**

```
streamlit>=1.32.0
reportlab>=4.0.0
pypdf>=4.0.0
PyGithub>=2.1.0
```

- [ ] **Schritt 2: .gitignore erstellen**

```
# Fertige Rechnungen nicht ins Repo (enthält personenbezogene Daten)
Fertige Rechnungen/

# macOS
.DS_Store

# Python
__pycache__/
*.pyc
.pytest_cache/

# Streamlit lokale Secrets
.streamlit/secrets.toml
```

- [ ] **Schritt 3: Commit**

```bash
git add requirements.txt .gitignore
git commit -m "chore: requirements und gitignore hinzugefuegt"
```

---

## Task 5: app.py – Login und Empfänger-Auswahl

**Files:**
- Create: `app.py`

- [ ] **Schritt 1: app.py mit Login-Logik erstellen**

Erstelle `app.py`:

```python
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
```

- [ ] **Schritt 2: App lokal testen**

```bash
streamlit run app.py
```

Im Browser prüfen:
- Passwortfeld erscheint
- Nach richtigem Passwort: zwei Schaltflächen sichtbar
- Beide Schaltflächen reagieren auf Klick

Mit `Ctrl+C` stoppen.

- [ ] **Schritt 3: Commit**

```bash
git add app.py
git commit -m "feat: Streamlit-App mit Login und Empfaenger-Auswahl"
```

---

## Task 6: app.py – Formular und Rechnungserstellung

**Files:**
- Modify: `app.py`

- [ ] **Schritt 1: Formular-Funktion am Ende von app.py ergänzen**

Ersetze den Block `else: # Formular wird in Task 6 ergänzt` (die letzten 3 Zeilen) in `app.py` durch:

```python
else:
    repo = verbinde_repo(st.secrets["GITHUB_TOKEN"], st.secrets["GITHUB_REPO"])
    zeige_formular(repo)
```

Füge außerdem die Funktion `zeige_formular()` **vor** dem `# ── Haupt-Routing ──`-Kommentar ein:

```python
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
```

- [ ] **Schritt 2: App lokal testen (ohne echte Secrets)**

```bash
streamlit run app.py
```

Prüfen dass:
- Nach Login die Empfänger-Auswahl erscheint
- Beide Pfade (neu / bestehend) das Formular anzeigen
- Bei bestehendem Kunden die Leistungstext-Frage erscheint
- Alle Felder korrekt vorausgefüllt sind
- "Zurück"-Button funktioniert

Mit `Ctrl+C` stoppen.

- [ ] **Schritt 3: Commit**

```bash
git add app.py
git commit -m "feat: Rechnungsformular mit Erstellungslogik"
```

---

## Task 7: GitHub-Repo einrichten und deployen

Dies sind manuelle Schritte die Marcel selbst durchführen muss (einmalige Einrichtung).

- [ ] **Schritt 1: Git-Repo initialisieren (falls noch nicht geschehen)**

```bash
cd "/Users/marcelsommer/Desktop/Rechnung auf Knopf druck "
git init
git add .
git commit -m "Initial commit: Rechnungs-Web-App"
```

- [ ] **Schritt 2: GitHub-Repo erstellen und pushen**

Im Terminal (Claude Code kann das ausführen):
```bash
gh repo create balance-rechnungen --private --push --source=.
```

- [ ] **Schritt 3: Gmail App-Passwort aktivieren**

1. Browser öffnen: `myaccount.google.com`
2. Sicherheit → 2-Schritt-Verifizierung aktivieren (falls noch nicht)
3. Sicherheit → App-Passwörter → Neues App-Passwort → Name: "Streamlit Rechnungen"
4. Das 16-stellige Passwort notieren

- [ ] **Schritt 4: GitHub Personal Access Token erstellen**

1. Browser: `github.com/settings/tokens/new`
2. Note: "Streamlit Rechnungen"
3. Ablauf: kein Ablauf (oder 1 Jahr)
4. Scope: nur `repo` ankreuzen
5. Token notieren (wird nur einmal angezeigt)

- [ ] **Schritt 5: Streamlit Cloud einrichten**

1. Browser: `share.streamlit.io` → "Sign in with GitHub"
2. "New app" → GitHub-Repo auswählen → Branch: `main` → Main file: `app.py`
3. "Advanced settings" → Secrets eintragen:

```toml
APP_PASSWORT = "hier_das_gewuenschte_passwort_fuer_den_kunden"
GMAIL_ABSENDER = "sommer.aeae@gmail.com"
GMAIL_APP_PASSWORT = "hier_das_16_stellige_app_passwort"
GITHUB_TOKEN = "hier_den_github_token"
GITHUB_REPO = "marcelsommer/balance-rechnungen"
```

4. "Deploy!" klicken
5. App-URL kopieren und an Kunden weitergeben

- [ ] **Schritt 6: Bestehende Kundendaten in GitHub schieben**

Die `Kunden/` JSON-Dateien sind lokal vorhanden und müssen einmalig committet werden:

```bash
git add Kunden/
git commit -m "chore: bestehende Kundendaten"
git push
```

---

## Abschluss-Checkliste

- [ ] `python -m pytest tests/ -v` → alle Tests grün
- [ ] App läuft lokal ohne Fehler
- [ ] GitHub-Repo ist erstellt und aktuell
- [ ] Streamlit Cloud zeigt die App an
- [ ] Einmal testweise eine Rechnung erstellen und prüfen ob Mail ankommt
