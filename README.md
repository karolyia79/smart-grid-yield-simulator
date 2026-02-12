# Smart Grid Yield Simulator (SGY) 🇭🇺

Ez egy Home Assistant egyedi integráció, amelyet kifejezetten a magyarországi napelemes (hibrid vagy szigetüzemű) rendszerekhez fejlesztettünk. Az integráció segít kiszámolni a valós pénzügyi megtakarítást a dinamikus tőzsdei áramárak (Nord Pool) és a rögzített rezsiárak (70.1 Ft/kWh) összevetésével.



## Főbb funkciók

* **Rugalmas Fázis-kezelés:** Támogatja az 1 fázisú, a 3 fázisú (egyben mért) és a fázisonkénti (L1, L2, L3 - pl. Shelly 3EM) mérést.
* **Valós Idejű Árkalkuláció:** Bruttó piaci ár (Ft/kWh) számítása Nord Pool adatokból, Fixer.io árfolyammal, 27% ÁFA-val és 25 Ft/kWh Rendszerhasználati Díjjal (RHD).
* **Inverter Hatékonyság:** Az inverter saját belső veszteség-szenzorának (W) támogatása a pontosabb rendszerkép érdekében.
* **Intelligens Tőzsdei Tanácsadó:** Javaslatot tesz az akkumulátor használatára, figyelembe véve a beállított **biztonsági tartalékot (kWh)**.
* **Hosszú távú Statisztika:** Automatikus napi, havi és éves megtakarítási számlálók a rezsiárhoz viszonyítva.

---

## Telepítési folyamat (Setup)

### 1. Előfeltételek
Mielőtt elkezdenéd, győződj meg róla, hogy a következő integrációk rendelkezésre állnak:
* **Nord Pool integráció:** HACS-ból telepítve és konfigurálva.
* **Fixer.io API kulcs:** Regisztrálj egy ingyenes kulcsot a [fixer.io](https://fixer.io/) oldalon.
* **Inverter szenzorok:** Pillanatnyi teljesítmény (W), napi összesített energia (kWh) és akkumulátor adatok.

### 2. Integráció hozzáadása a HACS-hoz
1.  Nyisd meg a Home Assistant-ot -> **HACS** -> **Integrations**.
2.  Jobb felső sarok (három pötty) -> **Custom repositories**.
3.  Másold be a repó URL-jét: `https://github.com/karolyia79/smart-grid-yield-simulator`
4.  Kategória: **Integration**, majd **ADD**.
5.  Töltsd le és **indítsd újra a Home Assistant-ot**.

### 3. Az integráció konfigurálása (UI Setup)
1.  **Settings** -> **Devices & Services** -> **ADD INTEGRATION**.
2.  Keress rá: `Smart Grid Yield Simulator`.
3.  Válaszd ki a fázisok számát (1 fázis, 3 fázis aggregált vagy L1/L2/L3 külön).
4.  Add meg a kért entitásokat (Nord Pool, Fixer API, Watt és kWh szenzorok).

---

## Dashboard Kártya Példa (YAML)

Másold be egy `Manual` kártyába. A `#` jellel jelölt sorokat cseréld ki a saját invertered entitásaira!



```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.dinamikus_brutto_aramar
        name: Bruttó Ár
        min: 0
        max: 120
        severity:
          green: 0
          yellow: 60
          red: 70.1
        needle: true
      - type: gauge
        entity: #sensor.inverter_load_power#
        name: Ház
        unit: W
        min: 0
        max: 5000
      - type: gauge
        entity: #sensor.inverter_battery_soc#
        name: Akku
        unit: "%"
        min: 0
        max: 100
        severity:
          red: 0
          yellow: 20
          green: 45
        needle: true
  - type: entities
    title: Mai Energia Forgalom
    show_header_toggle: false
    entities:
      - type: section
        label: Pillanatnyi Hálózat (W)
      # VÁLASZD A MEGFELELŐT A TELEPÍTÉS SZERINT:
      - entity: #sensor.grid_total_power# # Ha aggregált/1 fázisú
        name: Hálózat összesen
      # - entity: #sensor.grid_l1# # Ha fázisonkénti (L1, L2, L3)
      # - entity: #sensor.grid_l2#
      # - entity: #sensor.grid_l3#
      - type: section
        label: Napi Statisztika (kWh)
      - entity: #sensor.inverter_today_energy_import#
        name: Hálózatról vett
      - entity: #sensor.inverter_today_energy_export#
        name: Hálózatba eladott
      - entity: #sensor.inverter_today_production#
        name: Napelem mai termelés
      - entity: sensor.rendszer_pillanatnyi_vesztesege
        name: Inverter belső veszteség (W)
        icon: mdi:leak
  - type: entities
    title: Pénzügyi Szimuláció
    show_header_toggle: false
    entities:
      - entity: sensor.tozsdei_tanacsado
        name: Javaslat & Tartalék Infó
      - entity: sensor.pillanatnyi_megtakaritasi_sebesseg
        name: Pillanatnyi megtakarítás (Ft/h)
      - type: section
        label: Halmozott Megtakarítás
      - entity: sensor.napi_valos_nyereseg
        name: Ma megtermelt Ft
      - entity: sensor.havi_valos_nyereseg
        name: Ebben a hónapban Ft
      - entity: sensor.evi_valos_nyereseg
        name: Ebben az évben Ft
```

### Árkalkuláció (HUF/kWh):

A képlet biztosítja, hogy minden tag azonos mértékegységben (**Ft/kWh**) szerepeljen:

$$\text{Bruttó ár} = \left( \frac{\text{Spot}_{EUR/MWh} \times \text{Árfolyam}_{HUF/EUR}}{1000} \times 1.27 \right) + 25$$

| Tag | Jelentés | Egység |
| :--- | :--- | :--- |
| **Spot** | Nord Pool piaci ár | EUR/MWh |
| **1000** | MWh -> kWh váltószám | - |
| **1.27** | ÁFA (27%) | - |
| **25** | Rendszerhasználati díj | Ft/kWh |

## Licenc
MIT
