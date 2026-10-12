"""Prawo jako wymaganie architektury (art. 398 PKE): zakaz zimnego telefonu i zimnego maila.

Kanałów jest trzy i każdy ma podstawę. Modułu wysyłki zimnych wiadomości nie ma z założenia:
próba użycia innego kanału kończy się wyjątkiem, nie ostrzeżeniem.
"""

KANALY_DOZWOLONE = {
    "wizyta": "osobista wizyta, rozmowa twarzą w twarz",
    "polecenie": "kontakt na prośbę osoby polecającej, za wiedzą zainteresowanego",
    "formularz_klienta": "klient sam wypełnił formularz i wyraził zgodę",
}


class ZimnyKontakt(Exception):
    """Próba kontaktu kanałem bez podstawy prawnej."""


def zaplanuj_kontakt(lead: dict, kanal: str) -> dict:
    if kanal not in KANALY_DOZWOLONE:
        raise ZimnyKontakt(f"kanał '{kanal}' jest zakazany: numer czy adres z rejestru lub Map nie jest zgodą")
    if kanal == "formularz_klienta" and not lead.get("zgoda_z_formularza"):
        raise ZimnyKontakt("formularz bez zapisanej zgody klienta")
    return {"lead": lead["id"], "kanal": kanal, "podstawa": KANALY_DOZWOLONE[kanal]}
