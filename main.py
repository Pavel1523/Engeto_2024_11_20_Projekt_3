# projekt_3.py: třetí projekt do Engeto Online Python Akademie
# autor : Ing. Pavel Mrkva
# email: pavel.mrkva@seznam.cz


import sys
import csv
import requests as r
from bs4 import BeautifulSoup as bs
import logging
from urllib.parse import urlparse


def nastav_logovani() -> None:
    """Generuje a vypisuje průběh běhu skriptu."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def kontrola_dostupnosti_serveru(odkaz: str) -> bool:
    """Kontroluje dostupnost URL."""
    try:
        odpoved = r.get(odkaz, timeout=10)
        if odpoved.status_code == 200:
            return True
    except r.RequestException as e:
        logging.error(f"Chyba při připojení k URL {odkaz}: {e}")
    return False


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


def kontrola_reakce_serveru(odkaz: str) -> r.Response | None:
    """Kontrola prodlevy reakce serveru."""
    try:
        return r.get(
            odkaz, timeout=10
        )  # do 10 sec. od požadavku musí server reagovat a vratit data
    except r.RequestException as e:
        logging.error(f"Chyba při získávání dat z '{odkaz}': {e}")
        return None


def generovani_soup(res: r.Response | None) -> bs | None:
    """Převod html do objektu beautifulsoup."""
    return bs(res.text, "html.parser") if res else None


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


def cistit_cislo(text: str) -> str:
    """Odstraní z textu nevhodnou část (html-mezera -> znak na výstupu)."""
    return (
        text.replace("\xa0", "").replace(" ", "") if text else ""
    )  # odstraní nevhodnou část textu vzniklou zadáním mezery v html


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


def zapis_do_csv(data: list[dict[str, str]], jmeno_souboru: str) -> None:
    """Zapisuje výsledky scrapování do soubou *.csv."""
    try:
        with open(
            jmeno_souboru, mode="w", encoding="utf-8", newline=""
        ) as csv_soubor:
            zapis = csv.DictWriter(csv_soubor, fieldnames=data[0].keys())
            zapis.writeheader()
            zapis.writerows(data)
        logging.info(f"Data se zapsala do souboru: '{jmeno_souboru}'.")
    except Exception as e:
        logging.error(f"Chyba při zápisu do souboru: {e}!")


def scraping() -> None:
    """Procedura scrapování."""
    nastav_logovani()  # počátek loggování

    if not kontrola_na_vstupu(sys.argv):  # kontrola vstupních argumentů
        sys.exit(1)
    odkaz_stranky: str = sys.argv[1]  # vstupní parametr č. 1
    nazev_souboru: str = sys.argv[2]  # vstupní parametr č. 2
    seznam: list[dict[str, str]] = (
        []
    )  # list, do kterého se postupně zapisují slovníky s daty
    odpoved_1: r.Response | None = kontrola_reakce_serveru(
        odkaz_stranky
    )  # další kontrola serveru před zahájením scrapování včetně získání html
    if not odpoved_1:
        sys.exit(1)
    logging.info("Úvodní sekvence je v pořádku, scraping je zahájen!")

    soup_1: bs | None = generovani_soup(
        odpoved_1
    )  # převedení html úvodní url na objekt bs
    tables: list = filtr_vsechny_tagy(
        soup_1, "table"
    )  # selekce tagů na úvodní url s atributem "table", které obsahují požadované údaje (kód obce, název obce, link na obec)

    logging.info("Stahují se data ze serveru, čekej ...")

    for table in tables:  # procházíme všechny tabulky úvodního url

        for row in filtr_vsechny_tagy(
            table, "tr"
        ):  # výběr řádků postupně všech tabulek v úvodní url
            td_tags = row.find_all(
                "td", ["cislo", "overflow_name"]
            )  # získání dat ve sloupcích všech tabulek v uvodní url
            if td_tags:
                obec_odkaz: str = generovani_odkazu_k_obci(
                    "https://volby.cz/pls/ps2017nss/", td_tags[0].a.get("href")
                )  # url na jednotlivé obce (ukryto v atributu "a" ve sloupci  class="číslo")
                odpoved_2 = kontrola_reakce_serveru(
                    obec_odkaz
                )  # kontrola reakce serveru na url postupně každé obce
                soup_2 = generovani_soup(
                    odpoved_2
                )  # převedení html každé jednotlivé obce  na objekt bs
                tables = filtr_vsechny_tagy(
                    soup_2, "table"
                )  # selekce tagů na url obce s atributem "table", které obsahují požadované údaje (počet voličů, vydané obálky.....)

                strany: dict[str, str] = (
                    {}
                )  # slovník  {"strana" : "počet hlasů"}

                for table in tables[
                    1:
                ]:  # procházím tabulky na url pro každou obec
                    for row in filtr_vsechny_tagy(
                        table, "tr"
                    ):  # procházím všechny řádky tabulek
                        column = filtr_vsechny_tagy(
                            row, "td"
                        )  # získávám sloupce v jednotlivých tabulkách na url obcí
                        if (
                            column
                            and len(column) > 2
                            and column[1].text != "-"
                        ):  # vybírám pouze tabulky se 3-mi neprázdnými sloupci, kde jsou údaje o počtu hlasů, které strany dostaly
                            strany[column[1].text] = column[
                                2
                            ].text  # název strany, počet hlasů
                vystup_txt: dict[str, str] = generovani_vysledku(
                    td_tags[0].text,
                    td_tags[1].text,
                    hledani_tagu_dle_volby(
                        tables[0], "td", {"headers": "sa2"}
                    ),
                    hledani_tagu_dle_volby(
                        tables[0], "td", {"headers": "sa3"}
                    ),
                    hledani_tagu_dle_volby(
                        tables[0], "td", {"headers": "sa6"}
                    ),
                    strany,
                )
                # získaná data postupně :
                #   "kod obce" (získán na vstupní url v rámci běhu 2.for-cyklu),
                #   "název obce" (získán na vstupní url v rámci běhu 2.for-cyklu),
                #   "voliči v seznamu" (získáno na url obce rámci běhu 2.for-cyklu ve sloupci s atributem {"headers": "sa2"}),
                #   "vydané obálky" (získáno na url obce rámci běhu 2.for-cyklu ve sloupci s atributem {"headers": "sa3"}),
                #   "platné hlasy" (získáno na url obce rámci běhu 2.for-cyklu ve sloupci s atributem {"headers": "sa6"}),
                #   "slovník strany" (získán na url obce v rámci běhu 3.for-cyklu)- ve funkci generovani_vysledku se ze slovníku tahají zvlášť klíče a zvlášť hodnoty

                seznam.append(vystup_txt)
    if (
        len(seznam) == 0
    ):  # pokud je seznam prázdný (nejčastěji špatným zadáním argumentu url)
        logging.error(f"Žádná data na výstupu, zkontroluj vstupní URL!")
        sys.exit(1)
    zapis_do_csv(seznam, nazev_souboru)

    logging.info("Scraping je ukončen!")


if __name__ == "__main__":
    scraping()