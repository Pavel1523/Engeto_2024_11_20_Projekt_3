*** UVODNÍ INFORMACE O PROJEKTU ***

projekt_3.py: třetí projekt do Engeto Online Python Akademie
autor : Ing. Pavel Mrkva
email: pavel.mrkva@seznam.cz


*** POPIS PROJEKTU ***

Pomocí modulu/skriptu získáme data, volební výsledky týkající se voleb do Poslanecké sněmovny Parlamentu České republiky metodou webscrapingu.
Tato data jsou zveřejněna na portále "volby.cz", na odkazu https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ.
Výstupem jsou volební výsledky každé obce České republiky ve formě dat uložených v  *.csv souboru, který umožňuje následné zpracování např. pomocí software MsExcel.


*** VSTUPNÍ ÚDAJE ***

Skript má následující vstupní údaje:
1. URL úvodní webové stránky, kde je uveden přehled obcí v daném okrese, např pro okres Hodonín je to odkaz https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6205

2. Název souboru, do kterého se mají získaná data zapsat a uložit. Soubor najdete ve stejném adresáři, kde budete mít nainstalovaný skript.


*** PŘÍPRAVA PROSTŘEDÍ PŘED SPUŠTĚNÍM SKRIPTU ***

Před samotným spuštěním skriptu je nutné vytvořit podmínky pro jeho fungování. Následující postup je platný pro platformu operačního systému Windows.


1. Vytvořte si adresář/složku projektu ve svém počítači.

2. Ve složce projektu si vytvořte virtuální prostředí. Virtuální prostředí se pro operační platformu Windows vytvoří následujícím příkazem zadaným z příkazového řádku terminálu:
    """"""""""""""""""""""""""
    C:\......\složka_projektu>python -m venv <jmeno_virtualniho_prostredi>
    """"""""""""""""""""""""""

3. Aktivujte si nainstalované virtuální prostředí zadáním následujícího příkazu z příkazového řádku terminálu:
    """"""""""""""""""""""""""
    C:\......\složka_projektu\jmeno_virtualniho_prostredi\Scripts>activate.
    """"""""""""""""""""""""""
Pozor, příkaz se musí zadávat ze složky Script Vašeho virtuálního prostředí.

Po úspěšné aktivaci Vašeho virtuálního se změní příkazový řádek následovně:
    """"""""""""""""""""""""""
    (jmeno_virtualniho_prostredi)C:\......\složka_projektu\jmeno_virtualniho_prostredi\Scripts>
    """"""""""""""""""""""""""

4. Do složky projektu (!ne do složky virtuálního prostředí!) vložte následující soubory týkající se skriptu:
    - main.py
    - requirements.txt
    - README.md

5. Nainstalujte si v nutné externí knihovny uvedené v souboru requirements.txt spuštěním následujícího příkazu na příkazovém řádku terminálu při aktivovaném virtuálním prostředí:

    """"""""""""""""""""""""""
    (jmeno_virtualniho_prostredi)C:\......\složka_projektu>pip3 install -r requirements.txt
    """"""""""""""""""""""""""

Nově nainstalované knihovny se nainstalují do adresáře:

    C:\......\složka_projektu\jmeno_virtualniho_prostredi\Lib\site-packages

Jedná se o knihovny:
    - beautifulsoup4;
    - requests.
Pro zaručení instalace správné verze knihovny a tím správného běhu skriptu je důležité tyto knihovny instalovat spuštěním výše uvedeného příkazu.

6. Tímto máte vytvořeny podmínky pro běh skriptu.


*** SPUŠTĚNÍ SKRIPTU ***

Proces scrapování se spustí  zadáním příkazu z příkazového řádku  terminálu ve tvaru:

    """"""""""""""""""""""""""
    C:\......\složka_projektu>python main.py "argument_1" "argument_2"
    """"""""""""""""""""""""""

Argumenty se uvádí do uvozovek a  musí být ve tvaru:
1. argument_1:
Jedná se o odkaz na stránku, která je určena pro start skriptu. Jedná se vždy stránku

    """""""""""""""""""""
    Úvod > Poslanecká sněmovna 2017 > Výsledky hlasování – výběr územní úrovně > Okres Hodonín – výběr obce
    """"""""""""""""""""

Tato stránka se načte kliknutím na "X" ve sloupci výběr obce pro každý okres. Např. pro okres Hodonín se jedná o následující odkaz:
https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6205


2. argument_2
Zde zadáváte jméno souboru, do kterého se zpracovaná data načtou a uloží. Jedná se o soubor typu *.csv. Pozor, v zadání tohoto argumentu je nutné uvést také příponu ".csv". Pro přehlednost je doporučená forma tohoto argumentu ve tvaru <vysledky_okres>.csv psáno bez diakritiky. Např pro okres Hodonín potom:

    """""""""""""""""""""
    vysledky_hodonin.csv
    """"""""""""""""""""

Takže např. pro okres Hodonín bude příkaz znít následovně:

    """"""""""""""""""""""""""
    C:\......\složka_projektu>python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6205" "vysledky_hodonin.csv"
    """"""""""""""""""""""""""

*** BĚH SKRIPTU A KONTROLA BĚHU SKRIPTU ***

Běh skriptu je kontrolován na několika úrovních:
1. úvodní sekvence
    - kontrola správnosti zadaných vstupních argumentů
    - kontrola dostupnosti serveru a doby jeho reakce (implicitně nastaveno na 10 sec.)
2. následné sekvence
    - kontrola dostupnosti serveru a doby jeho reakce (implicitně nastaveno na 10 sec.) před zahájením scrapování
    - kontrola dostupnosti stránky odkazující na jednotlivé obce
    - kontrola objemu načtených dat před zápisem do *.csv

O průběhu skriptu je uživatel postupně informován výpisy do terminálu obsahující pro každou sekvenci:
- datum zahájení;
- čas zahájení;
- dobu trvání;
- typ informační zprávy (INFO, WARNING, ERROR, CRITICAL);
- text zprávy informující uživatele, jaká sekvence právě probíhá.

V případě jakékoli chyby skript také do terminálu vypíše, z jakého důvodu byl běh skriptu přerušen.


*** UKÁZKY BĚHU SKRIPTU ***

Níže uvedené ukázky se týkají scrapování výsledků voleb obcí v okrese Hodonín. 

1. Příkaz do příkazového řádku terminálu:

    """"""""""""""""""""""""""
    C:\......\složka_projektu>python main.py "https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6205" "vysledky_hodonin.csv"
    """"""""""""""""""""""""""

2. Postupné informační výpisy v případě bezchybného půběhu:

        ============================================================================================
        2025-03-26 11:07:05,587 - INFO - Provotní vstupní údaje prověřeny.
        2025-03-26 11:07:05,587 - INFO - Proces scrapování dat zahájen.
        2025-03-26 11:07:05,587 - INFO - Stahují se data ze serveru, čekej ...
        2025-03-26 11:07:35,518 - INFO - Data se zapsala do souboru: 'vysledky_hodonin.csv'
        2025-03-26 11:07:35,519 - INFO - Scraping je ukončen!
        ===========================================================================================

3. Příklady informačního výpisu pro chybová hlášení 
    - chybný argument č. 1
        2025-03-06 11:20:46, 373 - ERROR - Odkaz 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6205' není validní!
    
    - chybný argument č. 2
        2025-03-06 11:25:15, 747 - ERROR - Výstupní soubor musí mít příponu '.csv'!

    - chybný argument č. 1 (chybná jeho koncová část - subdoména)
        2025-03-06 11:35:15, 747 - ERROR - Nebyla získána žádná data! Zkontroluj vstupní URL!

    - příiš dlouhá doba reakce serveru 
        2025-03-06 11:45:15, 647 - ERROR - Chyba při získávání dat z 'https://www.volby.cz/pls/ps2017nss/ps32?xjazyk=CZ&xkraj=11&xnumnuts=6205': HTTPSConnectionPool(host='www.volby.cz', port=443): Read timed out. (timeout=10)!
    
    
4. Ukázka části výstupu

Výstup je zaznamenán v souboru 'vysledky_hodonin.csv'.
Soubor obsahuje data, která jsou na 83 řádcích, z nichž 1. řádek obsahuje záhlaví a zbývající 82 řádky obsahuje  konkrétní údaje.
Jednotlivá data jsou oddělena čárkou. 


Příklad prvních 6 řádků: 
    1. řádek .................záhlaví
    2. až 6. řádek............data výsledků voleb pro každou obec na samostatném řádku

        Kód obce,Název obce,Voliči v seznamu,Vydané obálky,Platné hlasy,Občanská demokratická strana,Řád národa - Vlastenecká unie,CESTA ODPOVĚDNÉ SPOLEČNOSTI,Česká str.sociálně demokrat.,Radostné Česko,STAROSTOVÉ A NEZÁVISLÍ,Komunistická str.Čech a Moravy,Strana zelených,"ROZUMNÍ-stop migraci,diktát.EU",Strana svobodných občanů,Blok proti islam.-Obran.domova,Občanská demokratická aliance,Česká pirátská strana,Referendum o Evropské unii,TOP 09,ANO 2011,Dobrá volba 2016,SPR-Republ.str.Čsl. M.Sládka,Křesť.demokr.unie-Čs.str.lid.,Česká strana národně sociální,REALISTÉ,SPORTOVCI,Dělnic.str.sociální spravedl.,Svob.a př.dem.-T.Okamura (SPD),Strana Práv Občanů,Národ Sobě
        586030,Archlebov,752,416,415,25,0,0,47,1,12,49,9,2,3,1,1,39,1,10,89,0,0,73,0,3,1,0,46,3,0
        586048,Blatnice pod Svatým Antonínkem,1733,1066,1055,101,1,1,70,4,50,61,7,9,42,0,2,74,2,40,247,0,2,199,0,7,2,1,133,0,0
        586056,Blatnička,356,239,238,16,0,0,14,0,10,17,3,0,1,0,0,23,0,4,58,0,5,42,0,0,0,2,43,0,0
        586072,Bukovany,618,380,372,35,0,0,43,0,5,42,4,5,3,0,0,52,0,9,78,0,1,53,1,0,1,0,39,1,0
        586081,Bzenec,3501,2016,2004,235,4,1,153,2,72,181,17,15,23,0,0,135,3,45,625,1,6,135,0,19,3,3,323,2,1


