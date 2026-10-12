"""Uruchamia scoring na data/kandydaci.json i zapisuje data/wynik.json.

Idempotencja: dwa przebiegi na tych samych danych dają identyczny plik. Data zmiany rusza się
tylko wtedy, gdy zmieniły się punkty.
"""
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline.scoring import score_lead  # noqa: E402


def przelicz(kandydaci, poprzedni, dzis):
    stare = {w["id"]: w for w in poprzedni}
    wynik = []
    for k in kandydaci:
        s = score_lead(k, dzis)
        zmiana = dzis.isoformat()
        if k["id"] in stare and stare[k["id"]]["punkty"] == s:
            zmiana = stare[k["id"]]["zmiana"]          # punkty bez zmian: data stoi
        wynik.append({"id": k["id"], "nazwa": k["nazwa"], "etap": k["etap"],
                      "wejscia": k["wejscia_na_prototyp"], "punkty": s, "zmiana": zmiana})
    return sorted(wynik, key=lambda w: -w["punkty"]["suma"])


def main(dzis=date(2026, 10, 12)):
    dane = json.loads((ROOT / "data" / "kandydaci.json").read_text(encoding="utf-8"))
    sciezka = ROOT / "data" / "wynik.json"
    poprzedni = json.loads(sciezka.read_text(encoding="utf-8")) if sciezka.exists() else []
    wynik = przelicz(dane, poprzedni, dzis)
    sciezka.write_text(json.dumps(wynik, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for w in wynik:
        p = w["punkty"]
        luka = "do zmierzenia" if p["do_zmierzenia"] else p["luka"]
        print(f"{p['suma']:>3}  {p['kategoria']:<14} {w['nazwa']:<34} popyt={p['popyt']} luka={luka} decydent={p['decydent']}")


if __name__ == "__main__":
    main()
