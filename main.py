# projekt_3.py: třetí projekt do Engeto Online Python Akademie
# Verze č.3 - upgrade po hodnocení
# autor : Ing. Pavel Mrkva
# email: pavel.mrkva@seznam.cz

import sys
import csv
import time
import logging
from urllib.parse import urlparse

import requests as r
from bs4 import BeautifulSoup as bs, Tag


def kontrola_konzistence_verze_pythonu(barvy: dict[str, str]) -> None:
    """Ověří, zda verze Pythonu splňuje minimální požadavek (3.13.0)."""
    if sys.version_info < (3, 13, 0):
        print(barvy["R"] + "=" * 90)
        print("Tento skript vyžaduje Python ve verzi 3.13.0 nebo vyšší!")
        print(f"Aktuální verze: {sys.version.split()[0]}")
        print("=" * 90 + barvy["RE"])
        raise SystemExit(1)


def nastav_logovani() -> None:
    """Generuje a vypisuje průběh běhu skriptu."""
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )


def inicializace(
    sys_argv: list[str], barvy: dict[str, str]
) -> tuple[str, str]:
    """Ověřuje správnost vstupních argumentů."""
    if not kontrola_na_vstupu(sys_argv):
        raise SystemExit(
            f"{barvy['R']}Neplatné vstupní argumenty!\n{barvy['RE']}"
            + 90 * "="
        )
    return sys_argv[1], sys_argv[2]


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
        if odpoved.ok:  # pokud odpověď je v rozsahu 2xx (tj. je OK)
            return True
    except r.RequestException as e:
        logging.error(f"Chyba při připojení k URL {odkaz}: {e}")
    return False


def kontrola_reakce_serveru(odkaz: str) -> r.Response | None:
    """Kontrola prodlevy reakce serveru s opakováním."""
    for pokus in range(3):  # máme 3 pokusy k navázání spojení se serverem
        try:
            odpoved = r.get(odkaz, timeout=10)
            if odpoved.ok:  # pokud odpověď je v rozsahu 2xx (tj. je OK)
                return odpoved
            logging.warning(
                "Neúspěšný pokus"
                f" {pokus + 1}/3: Server vrátil"
                f" {odpoved.status_code}"
            )
        except r.RequestException as e:
            logging.error(
                f"Chyba při získávání dat ({pokus + 1}/3) z '{odkaz}': {e}"
            )
        time.sleep(2)  # pauza mezi pokusy
    return None


def generovani_soup(res: r.Response | None) -> bs | None:
    """Převod html do objektu beautifulsoup."""
    return bs(res.text, "html.parser") if res else None


def ziskani_seznamu_obci(
    odkaz_stranky: str, barvy: dict[str, str]
) -> list[Tag]:
    """Stahuje HTML se seznamem obcí a převede jej na 'soup'."""
    odpoved = kontrola_reakce_serveru(odkaz_stranky)
    if not odpoved:
        raise SystemExit(
            f"{barvy['R']}Chyba: nelze získat odpověď ze serveru {odkaz_stranky}\n{barvy['RE']}"
            + "=" * 90
        )
    soup = generovani_soup(odpoved)
    return filtr_vsechny_tagy(soup, "table")


def zpracuj_obec(radek: Tag) -> dict[str, str] | None:
    """Extrahuje kód obce, název obce a odkaz na detailní stránku výsledků a volá 'def scrapuj_obec'"""
    td_tags = radek.find_all("td", ["cislo", "overflow_name"])
    if not td_tags or not td_tags[0].a:
        return None
    obec_odkaz = generovani_odkazu_k_obci(
        "https://volby.cz/pls/ps2017nss/", td_tags[0].a.get("href")
    )
    return scrapuj_obec(obec_odkaz, td_tags)


def scrapuj_obec(obec_odkaz: str, td_tags: list[Tag]) -> dict[str, str]:
    """Používá zadaný odkaz na detailní stránku obce, stáhne ji, extrahuje z ní počet voličů, platné hlasy a výsledky politických stran, a vrátí vše jako slovník."""
    odpoved = kontrola_reakce_serveru(obec_odkaz)
    soup = generovani_soup(odpoved)
    tabulky = filtr_vsechny_tagy(soup, "table")
    strany = zpracuj_strany(tabulky[1:])
    return generovani_vysledku(
        td_tags[0].text,  # kód obce
        td_tags[1].text,  # název obce
        hledani_tagu_dle_volby(
            tabulky[0], "td", {"headers": "sa2"}
        ),  # voliči v seznamu
        hledani_tagu_dle_volby(
            tabulky[0], "td", {"headers": "sa3"}
        ),  # vydané obálky
        hledani_tagu_dle_volby(
            tabulky[0], "td", {"headers": "sa6"}
        ),  # platné hlasy
        strany,
    )


def filtr_vsechny_tagy(tag: bs | Tag | None, typ: str) -> list[Tag] | None:
    """Filtruje a vrací všechny tagy dle zvoleného filtru/filtrů."""
    return tag.find_all(typ) if tag else None


def hledani_tagu_dle_volby(
    tag: bs | Tag | None, hledany_tag: str, attr: dict[str, str]
) -> Tag | None:
    """Filtruje a vrací první tag dle zvoleného filtru/filtrů."""
    return tag.find(hledany_tag, attr) if tag else None


def generovani_odkazu_k_obci(base_url: str, cast_odkazu: str) -> str:
    """Generuje URL ze dvou dílčích vstupů - prvotního URL a získaného odkazu/stringu/ ."""
    return f"{base_url}{cast_odkazu}"


def zpracuj_strany(tabulky: list[Tag]) -> dict[str, str]:
    """Získá volební výsledky strany a vrátí je jako slovník jméno:výsledky."""
    strany = {}  # slovník  {"strana" : "počet hlasů"}
    for tabulka in tabulky:  # procházím tabulky na url pro každou obec
        for radek in filtr_vsechny_tagy(
            tabulka, "tr"
        ):  # procházím všechny řádky tabulek
            sloupec = filtr_vsechny_tagy(
                radek, "td"
            )  # získávám sloupce v jednotlivých tabulkách na url obcí
            if (
                sloupec and len(sloupec) > 2 and sloupec[1].text != "-"
            ):  # vybírám pouze tabulky se 3-mi neprázdnými sloupci, kde jsou údaje o počtu hlasů, které strany dostaly

                strany[sloupec[1].text] = sloupec[
                    2
                ].text  # název strany, počet hlasů
    return strany


def scrapuj_vsechny_obce(tabulky: list[Tag]) -> list[dict[str, str]]:
    """Projde všechny tabulky a z každého řádku získá data o obci."""
    seznam = []
    for tabulka in tabulky:
        for radek in filtr_vsechny_tagy(tabulka, "tr"):
            vystup_txt = zpracuj_obec(radek)
            if vystup_txt:
                seznam.append(vystup_txt)
    return seznam


def generovani_vysledku(
    kod_obce: str,
    nazev_obce: str,
    volici_v_seznamu: Tag | None,
    vydane_obalky: Tag | None,
    platne_hlasy: Tag | None,
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


def zapis_do_csv(
    data: list[dict[str, str]], jmeno_souboru: str, barvy: dict[str, str]
) -> None:
    """Zapisuje výsledky scrapování do soubou *.csv."""
    try:
        with open(
            jmeno_souboru, mode="w", encoding="utf-8", newline=""
        ) as csv_soubor:
            zapis = csv.DictWriter(csv_soubor, fieldnames=data[0].keys())
            zapis.writeheader()
            zapis.writerows(data)
        logging.info(
            f"Data se zapsala do souboru: {barvy['G']}'{jmeno_souboru}'{barvy['RE']}."
        )
    except Exception as e:
        logging.error(f"Chyba při zápisu do souboru: {e}!")


def main() -> None:
    """Hlavní funkce."""
    barvy = {
        "R": "\033[31m",  # červená
        "G": "\033[032m",  # zelená
        "RE": "\033[0m",  # reset
    }

    kontrola_konzistence_verze_pythonu(barvy)

    nastav_logovani()
    print(90 * "=")
    odkaz_stranky, nazev_souboru = inicializace(
        sys.argv, barvy
    )  # předání sys.argv
    tabulky = ziskani_seznamu_obci(odkaz_stranky, barvy)
    logging.info("Prvotní vstupní údaje prověřeny.")
    logging.info("Proces scrapování dat zahájen.")
    logging.info("Stahují se data ze serveru, čekej ...")

    seznam = scrapuj_vsechny_obce(tabulky)

    if not seznam:
        logging.error(
            f"{barvy['R']}Nebyla získána žádná data! Zkontroluj vstupní URL!\n{barvy['RE']}"
            + 90 * "="
        )
        raise SystemExit(1)
    zapis_do_csv(seznam, nazev_souboru, barvy)
    logging.info(f"{barvy['G']}Scraping je ukončen!{barvy['RE']}")
    print(90 * "=")


if __name__ == "__main__":
    main()







#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    
# Hodnotitel tvého projektu: Matouš Holinka

# !matous
# Dne> 11.4.2025

# Pozitiva:
# Pěkné unpackování hodnot dict, řádek 203.
# skvělá aplikace metody writerows, řádek 224.

# Co by šlo vylepšit:
#   *   nevalidní knihovny pro projekt, requirements.txt. Txt soubor má obsahovat POUZE knihovny s projektem související.

#   *   nespecifikovaná minimální verze Pythonu, obecně. Používáš prvky novějších verzí Pythonu (type hintování bs | None), které není ve starších verzích podporováno. Doporučuji buď připsat do požadavků minimální verzi, nebo řešení type hints upravit pro starší verze.

#   *   poměrně dlouhé řešení skriptu (nad >200 řádků). Čím delší zápis, tím méně přehledný a pochopitelný se může stát. Toto není ani tak možnost zlepšení, spíš jako poznámka do budoucna.

#  *    sekce knihoven, řádek 6. V pořádku, ohlášení jsou na ůvodu souboru. Obvykle je ale řadíš nejprve standardní knihovny, následně knihovny třetích stran a finálně lokální moduly(víc na toto téma najdeš [1]). Případně já pracuji rád s knihovnou isort, seřadí vzorově za tebe:

#       import sys
#       import csv
#       import time
#       import logging
#       from urllib.parse import urlparse
    
#       import requests as r
#       from bs4 import BeautifulSoup as bs

#   *   dlouhé řádky, řádek 61, 83, .. . Maximální délka řádku by měla být 79 znaků (dokumenace [2]). Vždycky můžeš řádky elegantně zalamovat:
# logging.warning("Neúspěšný pokus"
#                 f" {attempt + 1}/3: Server vrátil"
#                 f" {odpoved.status_code}")

#  *    mix názvosloví CZ a EN, obecně. Pracuješ s českými komentáři a jmény funkcí ale současně anglickými odkazy. Vlastně je jedno, který si vybereš, ale vždy zůstaň konzistentní a pracuj s jedním. Tak, aby případný čtenář tvého kódu neměl problém pochopit, co jak označuješ.

#   *  mix uvozovek, obecně. Doporučuji vybrat jedny a ty používat všude. Nemíchat to. Ideálně si na to nachystat nějaký formátovač, který to bude hlídat za tebe.

#   *   nekonzistentní type hints, řádek 112. Buď je piš všude, nebo je nepiš jinde. Ani jedno není špatně a skoro bych řekl, že je důležitější, mít zápis konzistentní. Netřeba to přehánět, stačí obyč. list a tuple, pokud víš, že některé hodnoty bude nestované a složitější.

#   *   lokální rámec pracuje s proměnnou bez parametru, řádek 26. Tady doporučuji neohýbat chování interpreta a zadat sys.argv jako argument.

#   *   striktní stavový kód, řádek 68, 80. Ten je občas docela proradný, protože ti nemusí chodit jen 200, ale třeba 201, nebo 203, atd. Doporučuji metodu: if odpoved.ok:.

#   *   nejasná návratová hodnota, řádek 116, 147. Ohlášení return {} není příliš vhodné. Ideálně bych potenciální absenci hodnoty napsal přes None. Tedy ve tvém případě jako return None.

#   *   nadbytečné přepisování hodnot R, G, RE, obecně. Definuješ je tu na několika místech. Doporučuji zadat je jednou (ideálně main) a potom je posílat jako argumenty dál, kam bude potřeba.

#   *   procesní logika ve smyčce, řádek 244. Smyčka určitě nebude mezi spouštěcími příkazy/ohlášeními. Určitě bych i ji schoval do další doplněné uživatelské funkce.

# Závěrem:
# Strohé hodnocení neprogramátora: projekt jsi úspěšně splnil. Dělal přesně to, co zadání ukládá. Pojďme se ale spolu podívat ještě na nějaké detaily. Jako seniorní vývojář jsem tam zahlédl pár věcí, o kterých by bylo fajn si povědět.

# Prosím, nelekni se mých poznámek. Nejde o zásadní nedostatky, pouze doporučení, která ti mohou do budoucna pomoci a za které bych byl já sám moc rád, kdyby mi je tehdy někdo předal.

# Prosím, podruhé, pokud máš 2 minutky, ohodnoť můj přístup k hodnocení. Pokud se ti něco nelíbilo, nebo nesouhlasíš, dej mi to určitě vědět. Tady je link [3].


# Kdyby tě cokoliv zajímalo, neváhej mi napsat na Discordu. Zdraví tě a hodně úspěchu přeje, Matouš.

# [1] https://peps.python.org/pep-0008/#imports
# [2] https://peps.python.org/pep-0008/#maximum-line-length
# [3] https://forms.gle/u4rVR1gPUSwxNqDE6