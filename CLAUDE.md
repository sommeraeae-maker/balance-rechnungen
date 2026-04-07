# Rechnung auf Knopfdruck – BALANCE Vital-Lounge

## Was dieses Projekt macht
Automatische Rechnungserstellung für die BALANCE Vital-Lounge Hofgeismar.
Der Nutzer tippt `/rechnung`, gibt Empfänger, Leistung und Betrag ein – Claude erstellt eine fertige PDF auf dem Briefbogen.

## Ordnerstruktur
- `Rechnungstemplate/` → Briefbogen-PDF (NIEMALS verändern)
- `Fertige Rechnungen/` → fertige Rechnungs-PDFs (Output)
- `counter.json` → speichert die letzte Rechnungsnummer (fortlaufend)
- `rechnung_erstellen.py` → Hauptskript (Python 3, reportlab + pypdf)

## Workflow bei /rechnung
1. Empfänger fragen (Name + Adresse)
2. Leistungsbeschreibung fragen
3. Betrag fragen
4. Netto oder Brutto fragen → MwSt entsprechend berechnen
5. Skript aufrufen → PDF wird in `Fertige Rechnungen/` gespeichert

## Skript aufrufen
```bash
python3 "/Users/marcelsommer/Desktop/Rechnung auf Knopf druck /rechnung_erstellen.py" \
  "<Empfängername>" \
  "<Adresszeile1>|<Adresszeile2>" \
  "<Leistungsbeschreibung>" \
  "<Betrag>" \
  "<netto oder brutto>"
```

## MwSt-Logik
- Netto → + 19% = Brutto
- Brutto → ÷ 1,19 = Netto; Brutto − Netto = MwSt

## Rechnungsnummer-Format
`RE-YYYY-NNN` (z. B. `RE-2026-001`) — bei Jahreswechsel automatisch zurückgesetzt

## Noch einzutragen (in rechnung_erstellen.py, oben im Konfigurationsblock)
- `STEUERNUMMER` → echte Steuernummer oder USt-IdNr.
- `IBAN`, `BIC`, `BANK` → echte Bankverbindung
- `letzteNummer` in counter.json → Startnummer setzen wenn nötig

## Sprache
Immer auf Deutsch antworten. Marcel ist Anfänger – einfach und klar erklären.
