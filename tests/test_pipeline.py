import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pipeline import legal, run_scoring, scoring  # noqa: E402

DZIS = date(2026, 10, 12)
KAND = json.loads((ROOT / "data" / "kandydaci.json").read_text(encoding="utf-8"))
PO_ID = {k["id"]: k for k in KAND}


def test_luka_jest_mnozona_przez_popyt_nie_dodawana():
    # firma bez strony: baza 40. Przy popycie 40/40 dostaje pełne 40, przy popycie 0 dostaje 0.
    mocny = scoring.score_lead(PO_ID["k2"], DZIS)       # popyt wysoki, brak strony
    slaby = scoring.score_lead(PO_ID["k3"], DZIS)       # prawie bez opinii, brak strony
    assert mocny["luka"] > slaby["luka"]
    assert slaby["luka"] == 0


def test_brak_strony_bez_popytu_to_nie_okazja():
    s = scoring.score_lead(PO_ID["k3"], DZIS)
    assert s["suma"] < 30 and s["kategoria"] == "zimny"


def test_luka_niezmierzona_jest_pusta_a_nie_zerowa():
    s = scoring.score_lead(PO_ID["k4"], DZIS)           # strona jest, ale nic nie zmierzono
    assert s["luka"] is None and s["do_zmierzenia"] is True
    assert s["luka_zero"] is False


def test_brak_roku_w_stopce_nie_dowodzi_swiezej_strony():
    pkt, zero = scoring.score_luka("x.example", True, True, None, DZIS)
    assert pkt is None and zero is False


def test_zmierzona_zerowa_luka_jest_zerem():
    pkt, zero = scoring.score_luka("x.example", True, True, 2026, DZIS)
    assert pkt == 0 and zero is True


def test_stara_strona_bez_https_i_mobile_to_duza_luka():
    pkt, _ = scoring.score_luka("x.example", False, False, 2014, DZIS)
    assert pkt == 40


def test_firma_ktora_odpowiada_na_opinie_dostaje_punkty_popytu():
    a = scoring.score_popyt(100, 4.5, True, 10)
    b = scoring.score_popyt(100, 4.5, False, 10)
    assert a - b == 5


def test_punkty_nie_przekraczaja_maksimow():
    for k in KAND:
        s = scoring.score_lead(k, DZIS)
        assert s["popyt"] <= scoring.MAKS_POPYT
        assert (s["luka"] or 0) <= scoring.MAKS_LUKA
        assert s["decydent"] <= scoring.MAKS_DECYDENT


def test_scoring_jest_idempotentny_a_data_rusza_tylko_przy_zmianie_punktow():
    pierwszy = run_scoring.przelicz(KAND, [], DZIS)
    drugi = run_scoring.przelicz(KAND, pierwszy, date(2026, 10, 20))
    assert drugi == pierwszy                            # te same dane, ta sama data zmiany
    zmienione = [dict(k) for k in KAND]
    zmienione[0]["opinie"] = 5                          # spadek popytu
    trzeci = run_scoring.przelicz(zmienione, pierwszy, date(2026, 10, 20))
    nowy = next(w for w in trzeci if w["id"] == "k1")
    assert nowy["zmiana"] == "2026-10-20"
    reszta = [w for w in trzeci if w["id"] != "k1"]
    assert all(w["zmiana"] == "2026-10-12" for w in reszta)


@pytest.mark.parametrize("kanal", ["telefon_zimny", "email_zimny", "sms", "mailing"])
def test_zimne_kanaly_sa_zakazane(kanal):
    with pytest.raises(legal.ZimnyKontakt):
        legal.zaplanuj_kontakt(PO_ID["k1"], kanal)


@pytest.mark.parametrize("kanal", ["wizyta", "polecenie"])
def test_dozwolone_kanaly_przechodza(kanal):
    assert legal.zaplanuj_kontakt(PO_ID["k1"], kanal)["kanal"] == kanal


def test_formularz_wymaga_zapisanej_zgody():
    with pytest.raises(legal.ZimnyKontakt):
        legal.zaplanuj_kontakt(PO_ID["k1"], "formularz_klienta")
    assert legal.zaplanuj_kontakt(PO_ID["k5"], "formularz_klienta")["podstawa"]


def test_wysoka_ocena_bez_wolumenu_nie_jest_popytem():
    assert scoring.score_popyt(7, 5.0, False, 300) == 0
    assert scoring.score_popyt(30, 5.0, False, 300) == 20
