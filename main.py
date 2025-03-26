# projekt_3.py: třetí projekt do Engeto Online Python Akademie
# Verze č.2
# autor : Ing. Pavel Mrkva
# email: pavel.mrkva@seznam.cz

import sys
import csv
import time
import requests as r
from bs4 import BeautifulSoup as bs
import logging
from urllib.parse import urlparse


def nastav_logovani() -> None:
    """Generuje a vypisuje průběh běhu skriptu."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def inicializace() -> tuple[str, str]:
    """Ověřuje správnost vstupních argumentů."""
    R = "\033[31m"  # červená barva
    RE = "\033[0m"  # reset na výchozí barvu
    if not kontrola_na_vstupu(sys.argv):
        raise SystemExit(f"{R}Neplatné vstupní argumenty!\n{RE}" + 90 * "=")
    return sys.argv[1], sys.argv[2]


def kontrola_na_vstupu(sys_argv: list[str]) -> bool:
    """Kontrola vstupních údajů skriptu."""
    if (
        len(sys_argv) != 3
    ):  # kontrola počtu argumentů zadaných při spuštění skriptu
        logging.error(
            "Skript vyžaduje dva argumenty: URL a název CSV souboru."
        )
        return False
    odkaz_stranky: str = sys_argv[1]  # vstupní parametr
    nazev_souboru_csv: str = sys_argv[2]  # vstupní parametr

    parsed_url = urlparse(
        odkaz_stranky
    )  # kontrola platnosti jednotlivých částí vstupního url-argumentu
    if not (
        parsed_url.scheme
        and parsed_url.netloc
        and "volby.cz" in parsed_url.netloc
    ):
        logging.error(f"Odkaz '{odkaz_stranky}' není validní!")
        return False
    if not kontrola_dostupnosti_serveru(odkaz_stranky):  # viz popis funkce
        logging.error(f"Odkaz '{odkaz_stranky}' není dostupný!")
        return False
    if not nazev_souboru_csv.endswith(
        ".csv"
    ):  # cílový soubor musí mít příponu .csv
        logging.error("Výstupní soubor musí mít příponu '.csv'!")
        return False
    return True  # je True, pokud je všechno ve funkci True a umožní spuštění skriptu


def kontrola_dostupnosti_serveru(odkaz: str) -> bool:
    """Kontroluje dostupnost URL."""
    try:
        odpoved = r.get(odkaz, timeout=10)
        if odpoved.status_code == 200:
            return True
    except r.RequestException as e:
        logging.error(f"Chyba při připojení k URL {odkaz}: {e}")
    return False


def kontrola_reakce_serveru(odkaz: str) -> r.Response | None:
    """Kontrola prodlevy reakce serveru s opakováním."""
    for attempt in range(3):  # máme 3 pokusy k navázání spojení se serverem
        try:
            odpoved = r.get(odkaz, timeout=10)
            if odpoved.status_code == 200:
                return odpoved
            logging.warning(
                f"Neúspěšný pokus {attempt + 1}/3: Server vrátil {odpoved.status_code}"
            )
        except r.RequestException as e:
            logging.error(
                f"Chyba při získávání dat ({attempt + 1}/3) z '{odkaz}': {e}"
            )
        time.sleep(2)  # pauza mezi pokusy
    return None


def generovani_soup(res: r.Response | None) -> bs | None:
    """Převod html do objektu beautifulsoup."""
    return bs(res.text, "html.parser") if res else None


def ziskani_seznamu_obci(odkaz_stranky: str) -> list:
    """Stahuje HTML se seznamem obcí a převede jej na 'soup'."""
    R = "\033[31m"  # červená barva
    RE = "\033[0m"  # reset na výchozí barvu
    odpoved = kontrola_reakce_serveru(odkaz_stranky)
    if not odpoved:
        raise SystemExit(
            f"{R}Chyba: nelze získat odpověď ze serveru {odkaz_stranky}\n{RE}"
            + "=" * 90
        )
    soup = generovani_soup(odpoved)
    return filtr_vsechny_tagy(soup, "table")


def zpracuj_obec(row) -> dict[str, str]:
    """Extrahuje kód obce, název obce a odkaz na detailní stránku výsledků a volá 'def scrapuj_obec'"""
    td_tags = row.find_all("td", ["cislo", "overflow_name"])
    if not td_tags or not td_tags[0].a:
        return {}
    obec_odkaz = generovani_odkazu_k_obci(
        "https://volby.cz/pls/ps2017nss/", td_tags[0].a.get("href")
    )
    return scrapuj_obec(obec_odkaz, td_tags)


def scrapuj_obec(obec_odkaz: str, td_tags) -> dict[str, str]:
    """Používá zadaný odkaz na detailní stránku obce, stáhne ji, extrahuje z ní počet voličů, platné hlasy a výsledky politických stran, a vrátí vše jako slovník."""
    odpoved = kontrola_reakce_serveru(obec_odkaz)
    soup = generovani_soup(odpoved)
    tables = filtr_vsechny_tagy(soup, "table")
    strany = zpracuj_strany(tables[1:])
    return generovani_vysledku(
        td_tags[0].text,  # kód obce
        td_tags[1].text,  # název obce
        hledani_tagu_dle_volby(
            tables[0], "td", {"headers": "sa2"}
        ),  # voliči v seznamu
        hledani_tagu_dle_volby(
            tables[0], "td", {"headers": "sa3"}
        ),  # vydané obálky
        hledani_tagu_dle_volby(
            tables[0], "td", {"headers": "sa6"}
        ),  # platné hlasy
        strany,
    )


def filtr_vsechny_tagy(tag: bs | None, typ: str) -> list:
    """Filtruje a vrací všechny tagy dle zvoleného filtru/filtrů."""
    return tag.find_all(typ) if tag else []


def hledani_tagu_dle_volby(
    tag: bs | None, hledany_tag: str, attr: dict
) -> bs | None:
    """Filtruje a vrací první tag dle zvoleného filtru/filtrů."""
    return tag.find(hledany_tag, attr) if tag else None


def generovani_odkazu_k_obci(base_url: str, cast_odkazu: str) -> str:
    """Generuje URL ze dvou dílčích vstupů - prvotního URL a získaného odkazu/stringu/ ."""
    return f"{base_url}{cast_odkazu}"


def zpracuj_strany(tables) -> dict[str, str]:
    """Získá volební výsledky strany a vrátí je jako slovník jméno:výsledky."""
    strany = {}  # slovník  {"strana" : "počet hlasů"}
    for table in tables:  # procházím tabulky na url pro každou obec
        for row in filtr_vsechny_tagy(
            table, "tr"
        ):  # procházím všechny řádky tabulek
            column = filtr_vsechny_tagy(
                row, "td"
            )  # získávám sloupce v jednotlivých tabulkách na url obcí
            if (
                column and len(column) > 2 and column[1].text != "-"
            ):  # vybírám pouze tabulky se 3-mi neprázdnými sloupci, kde jsou údaje o počtu hlasů, které strany dostaly

                strany[column[1].text] = column[
                    2
                ].text  # název strany, počet hlasů
    return strany


def generovani_vysledku(
    kod_obce: str,
    nazev_obce: str,
    volici_v_seznamu: bs | None,
    vydane_obalky: bs | None,
    platne_hlasy: bs | None,
    strany: dict[str, str],
) -> dict[str, str]:
    """Generuje výsledky a zapisuje do připraveného slovníku."""
    return {
        "Kód obce": kod_obce,
        "Název obce": nazev_obce,
        "Voliči v seznamu": cistit_cislo(
            volici_v_seznamu.text if volici_v_seznamu else ""
        ),
        "Vydané obálky": cistit_cislo(
            vydane_obalky.text if vydane_obalky else ""
        ),
        "Platné hlasy": cistit_cislo(
            platne_hlasy.text if platne_hlasy else ""
        ),
        **{klic: cistit_cislo(hodnota) for klic, hodnota in strany.items()},
    }


def cistit_cislo(text: str) -> str:
    """Odstraní z textu nevhodnou část (html-mezera -> znak na výstupu)."""
    return (
        text.replace("\xa0", "").replace(" ", "") if text else ""
    )  # odstraní nevhodnou část textu vzniklou zadáním mezery v html


def zapis_do_csv(data: list[dict[str, str]], jmeno_souboru: str) -> None:
    """Zapisuje výsledky scrapování do soubou *.csv."""
    try:
        G = "\033[032m"  # zelená barva
        RE = "\033[0m"  # reset na výchozí barvu
        with open(
            jmeno_souboru, mode="w", encoding="utf-8", newline=""
        ) as csv_soubor:
            zapis = csv.DictWriter(csv_soubor, fieldnames=data[0].keys())
            zapis.writeheader()
            zapis.writerows(data)
        logging.info(f"Data se zapsala do souboru: {G}'{jmeno_souboru}'{RE}.")
    except Exception as e:
        logging.error(f"Chyba při zápisu do souboru: {e}!")


def main() -> None:
    """Hlavní funkce."""
    R = "\033[31m"  # červená barva
    G = "\033[032m"  # zelená barva
    RE = "\033[0m"  # reset na výchozí barvu
    nastav_logovani()
    print(90 * "=")
    odkaz_stranky, nazev_souboru = inicializace()
    seznam = []
    tables = ziskani_seznamu_obci(odkaz_stranky)
    logging.info("Prvotní vstupní údaje prověřeny.")
    logging.info("Proces scrapování dat zahájen.")
    logging.info("Stahují se data ze serveru, čekej ...")

    for table in tables:
        for row in filtr_vsechny_tagy(table, "tr"):
            vystup_txt = zpracuj_obec(row)
            if vystup_txt:
                seznam.append(vystup_txt)
    if not seznam:
        logging.error(
            f"{R}Nebyla získána žádná data! Zkontroluj vstupní URL!\n{RE}"
            + 90 * "="
        )
        raise SystemExit(1)
    zapis_do_csv(seznam, nazev_souboru)
    logging.info(f"{G}Scraping je ukončen!{RE}")
    print(90 * "=")


if __name__ == "__main__":
    main()