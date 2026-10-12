"""Demo: rejestr leadów z punktacją (firmy wymyślone). Zapisuje demo/leady.html i zrzut.

Uruchom: python demo/make_demo.py   (zrzut: playwright install chromium)
"""
import html
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import run_scoring  # noqa: E402

ETAPY = ["kandydat", "research", "prototyp", "wizyta", "oferta"]
KOLOR = {"gorący": "#FC6E08", "ciepły": "#0A95C9", "do podgrzania": "#7a8a99", "zimny": "#b4c0cc"}


def strona():
    import json
    dane = json.loads((ROOT / "data" / "kandydaci.json").read_text(encoding="utf-8"))
    wynik = run_scoring.przelicz(dane, [], date(2026, 10, 12))
    wiersze = []
    for w in wynik:
        p = w["punkty"]
        luka = "do zmierzenia" if p["do_zmierzenia"] else str(p["luka"])
        szer = f"{p['suma']}%"
        kolor = KOLOR[p["kategoria"]]
        etap = "".join(f"<i class='{'on' if ETAPY.index(w['etap']) >= j else ''}'></i>" for j in range(len(ETAPY)))
        wiersze.append(f"""<tr><td><b>{html.escape(w['nazwa'])}</b><small>etap: {w['etap']}</small></td>
<td><div class="sc"><span style="width:{szer};background:{kolor}"></span></div><b>{p['suma']}</b>
<span class="k" style="color:{kolor}">{p['kategoria']}</span></td>
<td>{p['popyt']}</td><td class="{'nm' if p['do_zmierzenia'] else ''}">{luka}</td><td>{p['decydent']}</td>
<td><div class="et">{etap}</div></td><td>{w['wejscia']}</td></tr>""")
    return f"""<!doctype html><html lang="pl"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Rejestr leadów</title>
<style>
:root{{--n:#0A95C9;--o:#FC6E08;--g:#021836}}
body{{margin:0;background:#f5f8fb;color:var(--g);font:15px/1.45 system-ui,Segoe UI,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:26px 20px 40px}}h1{{margin:0;font-size:26px}}.s{{color:#476;margin:2px 0 18px}}
table{{width:100%;border-collapse:collapse;background:#fff;border:1px solid #dbe4ec}}
th,td{{padding:10px 12px;border-bottom:1px solid #dbe4ec;text-align:left;vertical-align:middle}}
th{{background:#eaf3f9;font-size:13px}}td small{{display:block;color:#58708a}}
.sc{{width:110px;height:8px;background:#e3ebf2;border-radius:5px;overflow:hidden;display:inline-block;margin-right:8px}}
.sc span{{display:block;height:100%}}.k{{margin-left:6px;font-weight:600;font-size:13px}}
.nm{{color:var(--o);font-weight:600}}
.et{{display:flex;gap:4px}}.et i{{width:18px;height:8px;border-radius:3px;background:#dbe4ec}}.et i.on{{background:var(--n)}}
.note{{margin-top:14px;background:#fff;border:1px solid #dbe4ec;border-radius:10px;padding:10px 16px;color:#476;font-size:14px}}
</style></head><body><main>
<h1>Rejestr leadów (dane wymyślone)</h1>
<p class="s">Scoring: popyt (maks. 40) + luka pomnożona przez siłę popytu (maks. 40) + dostępność decydenta (maks. 20).</p>
<table><tr><th>Firma</th><th>Wynik</th><th>Popyt</th><th>Luka</th><th>Decydent</th><th>Etap</th><th>Wejścia na prototyp</th></tr>
{''.join(wiersze)}</table>
<div class="note">Luka "do zmierzenia" znaczy, że nie mamy pomiaru, a nie że strona jest dobra. Kontakt wyłącznie przez wizytę, polecenie albo formularz klienta ze zgodą. Zimnego telefonu i maila w systemie nie ma.</div>
</main></body></html>"""


if __name__ == "__main__":
    out = ROOT / "demo" / "leady.html"
    out.write_text(strona(), encoding="utf-8")
    print("zapisano", out.relative_to(ROOT))
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 700})
            pg.goto(out.as_uri())
            (ROOT / "screenshots").mkdir(exist_ok=True)
            pg.screenshot(path=str(ROOT / "screenshots" / "leady.png"), full_page=True)
            b.close()
        print("zrzut ok")
    except ImportError:
        print("brak playwright: pominięto zrzut")
