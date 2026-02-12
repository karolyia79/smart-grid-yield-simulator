# Smart Grid Yield Simulator (SGY) 🇭🇺

Ez egy Home Assistant egyedi integráció, amelyet kifejezetten a magyarországi napelemes (hibrid vagy szigetüzemű) rendszerekhez fejlesztettünk. Az integráció segít kiszámolni a valós pénzügyi megtakarítást és a tőzsdei elszámolás várható költségeit a dinamikus tőzsdei áramárak (Nord Pool) és a rögzített rezsiárak (70.1 Ft/kWh) összevetésével.

## Főbb funkciók

* **Valós Idejű Árkalkuláció:** Kiszámolja a bruttó piaci árat (Ft/kWh) a Nord Pool adatokból, a Fixer.io-ról származó EUR/HUF árfolyammal, 27% ÁFA-val és a 25 Ft/kWh Rendszerhasználati Díjjal (RHD).
* **Pillanatnyi Megtakarítás:** Megmutatja (Ft/h egységben), hogy az aktuális fogyasztásod mennyibe kerülne a tőzsdén a rezsiárhoz képest.
* **Napi Pénzügyi Mérleg (kWh alapon):** Az invertered által mért pontos napi import/export energia (kWh) alapján kiszámolja, mennyi lenne a mai napod tényleges költsége vagy bevétele tőzsdei elszámolásban.
* **Tőzsdei Tanácsadó:** Szöveges javaslatot ad az akkumulátor és a fogyasztók vezérléséhez (pl. extrém olcsó árnál töltés, drága árnál akku használat).
* **Hosszú távú Statisztika:** Automatikusan generált napi, havi és éves megtakarítási számlálók.

## Telepítés

### 1. Előfeltételek
A használathoz szükséged lesz:
1.  **Nord Pool Integrációra:** Telepítve és beállítva (HACS-ból elérhető).
2.  **Fixer.io API Kulcsra:** Ingyenesen regisztrálható a [fixer.io](https://fixer.io/) oldalon.
3.  **Inverter Szenzorokra:** * Pillanatnyi teljesítmény: Load (W) és Grid (W).
    * Napi összesített energia: Napi Import (kWh) és Napi Export (kWh).

### 2. Hozzáadás a HACS-hoz
1.  Nyisd meg a **HACS**-ot a Home Assistant-ban.
2.  Kattints a jobb felső sarokban a három pöttyre -> **Custom repositories**.
3.  Másold be az URL-t: `https://github.com/karolyia79/smart-grid-yield-simulator`
4.  Kategória: **Integration**.
5.  Telepítés után **indítsd újra a Home Assistant-ot**.

### 3. Konfiguráció
1.  **Beállítások** -> **Eszközök és szolgáltatások** -> **Integráció hozzáadása**.
2.  Keresd meg: **Smart Grid Yield Simulator**.
3.  Az űrlapon válaszd ki a megfelelő szenzorokat a legördülő listákból.

## Létrejövő entitások

| Entitás ID | Leírás | Egység |
| :--- | :--- | :--- |
| `sensor.dinamikus_brutto_aramar` | Aktuális piaci ár (ÁFA + RHD) | Ft/kWh |
| `sensor.napi_halozati_koltseg_tozsdei` | A mai importált energia tőzsdei ára | Ft |
| `sensor.napi_halozati_bevetel_tozsdei` | A mai exportált energia tőzsdei értéke | Ft |
| `sensor.elmeleti_nyereseg_merteke` | Különbség a rezsiár (70.1 Ft) és a tőzsde között | Ft/kWh |
| `sensor.pillanatnyi_megtakaritasi_sebesseg` | Pillanatnyi spórolás mértéke | Ft/h |
| `sensor.tozsdei_tanacsado` | Akkumulátor kezelési javaslat | - |
| `sensor.napi_valos_nyereseg` | Ma megspórolt forintok (rezsihez képest) | Ft |
| `sensor.euro_arfolyam` | A Fixer-től lekért aktuális árfolyam | Ft/EUR |

## Kiszámítási képlet
Az integráció a bruttó árat a következő módon kalkulálja:
$$\text{Bruttó ár} = \left( \frac{\text{NordPool (EUR/MWh)} \times \text{Fixer árfolyam} \times 1.27}{1000} \right) + 25$$

## Licenc
MIT
