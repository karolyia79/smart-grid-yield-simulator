# Smart Grid Yield Simulator (SGY) 🇭🇺

Ez egy Home Assistant egyedi integráció (Custom Component), amelyet kifejezetten a magyarországi napelemes (hibrid/szigetüzemű) rendszerekhez fejlesztettünk. Segít kiszámolni a valós pénzügyi megtakarítást a dinamikus tőzsdei áramárak (Nord Pool) és a rögzített rezsiárak (70.1 Ft/kWh) összevetésével.

## Főbb funkciók

* **Bruttó Árkalkuláció:** Kiszámolja a valós piaci árat (Ft/kWh) a Nord Pool adatokból, az aktuális EUR/HUF árfolyam (Fixer.io), a 27%-os ÁFA és a 25 Ft/kWh Rendszerhasználati Díj (RHD) figyelembevételével.
* **Valós Megtakarítás Számítása:** * A saját termelésből (nap/akku) való fogyasztást fix 70.1 Ft-os értéken számolja.
    * Hálózati vételezés esetén figyelembe veszi a tőzsdei ár és a 70.1 Ft közötti különbséget (nyereséget).
* **Tőzsdei Tanácsadó:** Szöveges javaslatot ad az akkumulátor kezelésére (Vétel, Tartás, Eladás).
* **Statisztika:** Automatikusan generált napi, havi és éves megtakarítási számlálók (Utility Meters).

## Telepítés

### 1. Előfeltételek
A használathoz szükséged lesz az alábbiakra:
1.  **Nord Pool Integráció:** Telepítve és konfigurálva (HACS-ból elérhető).
2.  **Fixer.io API Kulcs:** Ingyenesen regisztrálható a [fixer.io](https://fixer.io/) oldalon.
3.  **Inverter adatok:** Szenzorok a ház pillanatnyi fogyasztásához (Load) és a hálózati teljesítményhez (Grid).

### 2. Hozzáadás a HACS-hoz
1.  Nyisd meg a **HACS**-ot a Home Assistant-ban.
2.  Kattints a jobb felső sarokban a három pöttyre, majd a **Custom repositories** menüpontra.
3.  Másold be az URL-t: `https://github.com/karolyia79/smart-grid-yield-simulator`
4.  Kategóriának válaszd az **Integration**-t, majd kattints az **Add** gombra.
5.  Telepítsd a megjelenő integrációt, majd **indítsd újra a Home Assistant-ot**.

### 3. Konfiguráció az UI-n
1.  Menj a **Beállítások** -> **Eszközök és szolgáltatások** menübe.
2.  Kattints az **Integráció hozzáadása** gombra.
3.  Keresd meg a **Smart Grid Yield Simulator** nevet.
4.  Add meg a kért adatokat:
    * Fixer.io API kulcs
    * Nord Pool szenzor (EUR/MWh)
    * Inverter Load Power (W)
    * Inverter Grid Power (W)

## Létrejövő entitások

Az integráció a következő fix azonosítójú szenzorokat hozza létre:

| Entitás ID | Leírás | Egység |
| :--- | :--- | :--- |
| `sensor.dinamikus_brutto_aramar` | Bruttó piaci ár (ÁFA + RHD) | Ft/kWh |
| `sensor.elmeleti_nyereseg_merteke` | Különbség a 70.1 Ft-os árhoz képest | Ft/kWh |
| `sensor.pillanatnyi_megtakaritasi_sebesseg` | Pillanatnyi spórolás mértéke | Ft/h |
| `sensor.tozsdei_tanacsado` | Akkumulátor kezelési javaslat | - |
| `sensor.napi_valos_nyereseg` | Ma összesen megspórolt forint | Ft |
| `sensor.euro_arfolyam` | A Fixer-től lekért HUF/EUR árfolyam | Ft |

## Kiszámítási mód
Az integráció a bruttó árat az alábbi képlet alapján számolja:
$$\text{Bruttó ár} = \left( \frac{\text{NordPool (EUR/MWh)} \times \text{Árfolyam} \times 1.27}{1000} \right) + 25$$

## Licenc
MIT
