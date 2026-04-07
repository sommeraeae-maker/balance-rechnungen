# GitHub-Dienst: Zähler und Kundendaten aus dem GitHub-Repo lesen und schreiben
import json
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


def lese_kunden(repo) -> list:
    """Liest alle Kunden-JSON-Dateien aus Kunden/ und gibt sie als Liste zurück."""
    try:
        dateien = repo.get_contents("Kunden")
    except Exception:
        return []

    kunden = []
    for datei in dateien:
        if datei.name.endswith(".json"):
            inhalt = json.loads(datei.decoded_content)
            inhalt["_dateiname"] = datei.name
            kunden.append(inhalt)

    return sorted(kunden, key=lambda k: k.get("name", ""))


def speichere_kunde(repo, name: str, adresse: list, letzte_leistung: str):
    """Legt einen neuen Kunden an oder aktualisiert den bestehenden in Kunden/."""
    sicherer_name = name.replace(" ", "_").replace("/", "-").replace("\\", "-")
    pfad = f"Kunden/{sicherer_name}.json"

    inhalt = {
        "name": name,
        "adresse": adresse,
        "letzte_leistung": letzte_leistung,
    }
    inhalt_str = json.dumps(inhalt, indent=2, ensure_ascii=False)

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
