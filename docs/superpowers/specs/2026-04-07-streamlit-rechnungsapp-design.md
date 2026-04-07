# Design: Streamlit Rechnungs-Web-App
**Datum:** 2026-04-07  
**Projekt:** Rechnung auf Knopfdruck – BALANCE Vital-Lounge

---

## Ziel

Eine passwortgeschützte Web-App, die ein Kunde im Browser öffnen kann, um selbständig Rechnungen zu erstellen. Die fertige PDF wird automatisch per E-Mail an `umohr@balance-sonnenstudio.de` geschickt. Die Rechnungsnummerierung läuft nahtlos weiter.

---

## Architektur

```
GitHub-Repo
├── app.py                          (Streamlit-App – neu)
├── rechnung_erstellen.py           (unverändert übernommen)
├── counter.json                    (wird nach jeder Rechnung via GitHub API aktualisiert)
├── Rechnungstemplate/
│   └── Balance_HG_Briefpapier_A4_03'21_a.pdf
└── requirements.txt                (reportlab, pypdf, streamlit, PyGithub)
```

Hosting: **Streamlit Cloud** (kostenlos), verbunden mit GitHub-Repo.

---

## Komponenten

### 1. Passwortschutz (`app.py`)
- Beim ersten Aufruf sieht der Nutzer nur ein Passwortfeld
- Passwort wird gegen `st.secrets["APP_PASSWORT"]` geprüft
- Falsches Passwort: Fehlermeldung, kein Zugriff
- Richtiges Passwort: Session-State `eingeloggt = True`, Formular wird angezeigt

### 2. Empfänger-Auswahl (`app.py`)

Direkt nach dem Login sieht der Nutzer zwei Schaltflächen:

**[Neuer Rechnungsempfänger]** | **[Bestehender Rechnungsempfänger]**

**Pfad A – Neuer Empfänger:**
- Formular mit leeren Feldern: Name, Adresszeile 1, Adresszeile 2
- Leistungsbeschreibung, Betrag, Netto/Brutto
- Nach Erstellung: Kunde wird als JSON in `Kunden/` via GitHub API gespeichert
- JSON-Format: `{ "name": "...", "adresse": ["...", "..."], "letzte_leistung": "..." }`

**Pfad B – Bestehender Empfänger:**
- App liest alle JSON-Dateien aus `Kunden/` via GitHub API
- Auswahlfeld mit allen gespeicherten Kundennamen
- Nach Auswahl: Name und Adresse werden automatisch eingetragen
- App zeigt: *„Ist der Rechnungstext wieder: ‚[letzte_leistung]'?"*
  - **Ja** → Leistungsbeschreibung wird übernommen
  - **Nein** → leeres Textfeld erscheint zum neu schreiben
- Nach Erstellung: `letzte_leistung` in der Kunden-JSON via GitHub API aktualisiert

### 3. Rechnungsformular (`app.py`)
Felder (werden je nach Pfad A/B vorausgefüllt oder leer angezeigt):
- **Empfängername** (Textfeld, Pflichtfeld)
- **Adresszeile 1** (Textfeld, Pflichtfeld)
- **Adresszeile 2** (Textfeld, Pflichtfeld)
- **Leistungsbeschreibung** (mehrzeiliges Textfeld, Pflichtfeld)
- **Betrag** (Zahlenfeld, Pflichtfeld)
- **Netto oder Brutto** (Auswahlfeld: "Netto" / "Brutto")
- Button: "Rechnung erstellen"

### 4. Rechnungserstellung
- `rechnung_erstellen.py` wird als Python-Modul importiert (kein Subprocess)
- Die Funktion `erstelle_rechnung()` wird direkt aufgerufen
- Die PDF-Bytes werden im Arbeitsspeicher gehalten (kein Schreiben auf Streamlit-Disk)

**Anpassung an `rechnung_erstellen.py` nötig:**  
`erstelle_rechnung()` schreibt die PDF aktuell in `Fertige Rechnungen/` auf der lokalen Festplatte. Auf Streamlit Cloud gibt es keinen dauerhaften Ordner. Lösung: Eine zweite Funktion `erstelle_rechnung_bytes()` wird ergänzt, die die PDF-Bytes direkt zurückgibt ohne auf Disk zu schreiben. Die bestehende Funktion bleibt unverändert (für lokale Nutzung über Claude Code).

### 5. Rechnungsnummer via GitHub API
- Beim Start: `counter.json` direkt aus dem GitHub-Repo lesen (via PyGithub)
- Nach Erstellung: erhöhte Nummer als Commit zurückschreiben
- GitHub-Token wird in `st.secrets["GITHUB_TOKEN"]` gespeichert
- Repo-Name: `st.secrets["GITHUB_REPO"]` (z. B. `"marcelsommer/rechnungen"`)

### 6. E-Mail-Versand
- Bibliothek: `smtplib` (in Python eingebaut, kein extra Paket)
- Absender: `sommer.aeae@gmail.com`
- Gmail App-Passwort: `st.secrets["GMAIL_APP_PASSWORT"]`
- Empfänger: `umohr@balance-sonnenstudio.de` (fest eingetragen)
- Anhang: PDF-Bytes als `.pdf`-Datei
- Betreff: `Rechnung {rechnungsnummer} – BALANCE Vital-Lounge`

### 7. Erfolgsmeldung
- Nach erfolgreichem Versand: grüne Box mit Text:  
  `"Rechnung RE-2026-XXX wurde erfolgreich an umohr@balance-sonnenstudio.de geschickt."`
- Bei Fehler: rote Box mit Fehlerbeschreibung

---

## Zugangsdaten (Streamlit Secrets)

Werden **nie** im Code gespeichert, nur in den Streamlit Cloud Settings:

```toml
APP_PASSWORT = "..."
GMAIL_APP_PASSWORT = "..."
GITHUB_TOKEN = "..."
GITHUB_REPO = "marcelsommer/..."
```

---

## Ablauf (Schritt für Schritt)

1. Kunde öffnet App-URL im Browser
2. Passwort eingeben → bei Erfolg: Formular sichtbar
3. Felder ausfüllen, "Rechnung erstellen" klicken
4. App liest aktuelle Rechnungsnummer aus GitHub
5. PDF wird im Arbeitsspeicher erstellt (Briefbogen + Rechnungstext zusammengeführt)
6. Rechnungsnummer in GitHub hochgeschrieben
7. PDF per Gmail an `umohr@balance-sonnenstudio.de` verschickt
8. Erfolgsmeldung angezeigt

---

## Offene Schritte vor dem Start

- [ ] GitHub-Repo für die App anlegen (öffentlich oder privat)
- [ ] Gmail App-Passwort für `sommer.aeae@gmail.com` aktivieren
- [ ] GitHub Personal Access Token erstellen (nur `contents: write` Berechtigung)
- [ ] Streamlit Cloud Account anlegen und mit GitHub verbinden
- [ ] Secrets in Streamlit Cloud eintragen
