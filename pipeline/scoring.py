"""Scoring leadów w trzech bramkach: dowód popytu, widoczna luka, dostępność decydenta.

Luka jest MNOŻONA przez siłę popytu, nie dodawana: brak strony u firmy bez klientów nie jest okazją.
Gdy luki nie da się zmierzyć, wynik jest pusty (None), a nie zerowy.
"""
from datetime import date

MAKS_POPYT = 40
MAKS_LUKA = 40
MAKS_DECYDENT = 20
DNI_SWIEZEJ_OPINII = 60


def score_popyt(opinie: int, ocena: float, odpowiada_na_opinie: bool, dni_od_ostatniej: int) -> int:
    """Maks. 40. Najmocniejszy sygnał: firma już wydaje na klienta (odpowiada, ma świeże opinie)."""
    if opinie >= 200:
        opinie_pkt = 20
    elif opinie >= 80:
        opinie_pkt = 15
    elif opinie >= 30:
        opinie_pkt = 10
    elif opinie >= 10:
        opinie_pkt = 5
    else:
        opinie_pkt = 0
    # ocena bez wolumenu nic nie dowodzi: pięć gwiazdek z siedmiu opinii nie jest popytem
    ocena_pkt = 0 if opinie < 10 else 10 if ocena >= 4.5 else 6 if ocena >= 4.0 else 2 if ocena >= 3.5 else 0
    wydaje_pkt = (5 if odpowiada_na_opinie else 0) + (5 if dni_od_ostatniej <= DNI_SWIEZEJ_OPINII else 0)
    return opinie_pkt + ocena_pkt + wydaje_pkt


def score_luka(strona, https, responsywna, rok_stopki, dzis: date):
    """Zwraca (punkty bazowe albo None, luka_zero).

    None znaczy "do zmierzenia". Brak roku w stopce nie jest dowodem świeżej strony.
    """
    if not strona:
        return MAKS_LUKA, False
    pomiary = (https, responsywna, rok_stopki)
    if all(p is None for p in pomiary):
        return None, False
    pkt = 0
    if https is False:
        pkt += 10
    if responsywna is False:
        pkt += 15
    if rok_stopki is not None and dzis.year - rok_stopki >= 3:
        pkt += 15
    if pkt == 0 and any(p is None for p in pomiary):
        return None, False
    return pkt, pkt == 0


def score_decydent(wlasciciel_odpowiada: bool, godziny_kontaktu: bool, firma_jednoosobowa: bool) -> int:
    """Maks. 20: czy da się porozmawiać z osobą, która decyduje."""
    return (10 if wlasciciel_odpowiada else 0) + (5 if godziny_kontaktu else 0) \
        + (5 if firma_jednoosobowa else 0)


def score_lead(lead: dict, dzis: date) -> dict:
    punkty_popyt = score_popyt(lead["opinie"], lead["ocena"], lead["odpowiada_na_opinie"],
                               lead["dni_od_ostatniej_opinii"])
    s = lead.get("strona") or {}
    punkty_luka_bazowe, luka_zero = score_luka(lead.get("strona_url"), s.get("https"),
                                               s.get("responsywna"), s.get("rok_stopki"), dzis)
    # Bramka 2 skalowana bramką 1: pełna luka należy się tylko firmie z pełnym dowodem popytu.
    if punkty_luka_bazowe is None:
        punkty_luka = None                                 # luka niezmierzona: nie zerujemy
    else:
        punkty_luka = int(round(punkty_luka_bazowe * punkty_popyt / MAKS_POPYT))
    punkty_decydent = score_decydent(lead["wlasciciel_odpowiada"], lead["godziny_kontaktu"],
                                     lead["jednoosobowa"])
    suma = punkty_popyt + (punkty_luka or 0) + punkty_decydent
    return {"popyt": punkty_popyt, "luka": punkty_luka, "luka_zero": luka_zero,
            "decydent": punkty_decydent, "suma": suma, "do_zmierzenia": punkty_luka is None,
            "kategoria": kategoria(suma)}


def kategoria(suma: int) -> str:
    return "gorący" if suma >= 70 else "ciepły" if suma >= 50 else "do podgrzania" if suma >= 30 else "zimny"
