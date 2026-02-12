# Smart Grid Yield Simulator (SGY) 🇭🇺

Ez egy Home Assistant egyedi integráció, amelyet kifejezetten a magyarországi napelemes (hibrid vagy szigetüzemű) rendszerekhez fejlesztettünk. Az integráció segít kiszámolni a valós pénzügyi megtakarítást és a tőzsdei elszámolás várható költségeit a dinamikus tőzsdei áramárak (Nord Pool) és a rögzített rezsiárak (70.1 Ft/kWh) összevetésével.

## Főbb funkciók

* **Valós Idejű Árkalkuláció:** Bruttó piaci ár (Ft/kWh) számítása Nord Pool adatokból, Fixer.io árfolyammal, 27% ÁFA-val és 25 Ft/kWh Rendszerhasználati Díjjal (RHD).
* **Napi Pénzügyi Mérleg (kWh):** Az inverter pontos napi import/export adatai alapján számolt tényleges költség vagy bevétel tőzsdei áron.
* **Intelligens Tőzsdei Tanácsadó:** Javaslat az akkumulátor használatára, amely folyamatosan jelzi a beállított **biztonsági tartalékig (kWh)** hátralévő energiamennyiséget.
* **Hosszú távú Statisztika:** Automatikus napi, havi és éves megtakarítási számlálók (rezsiárhoz viszonyítva).

---

## Telepítési folyamat (Setup)

### 1. Előfeltételek
Mielőtt elkezdenéd, győződj meg róla, hogy a következő integrációk és adatok rendelkezésre állnak:
* **Nord Pool integráció:** HACS-ból telepítve és konfigurálva.
* **Fixer.io API kulcs:** Regisztrálj egy ingyenes kulcsot a [fixer.io](https://fixer.io/) oldalon.
* **Inverter szenzorok:** Szükséged lesz a pillanatnyi teljesítmény (W), a napi összesített energia (kWh) és az akkumulátor töltöttség (%) szenzorokra.

### 2. Integráció hozzáadása a HACS-hoz
1. Nyisd meg a Home Assistant-ot, és menj a **HACS** menüpontba.
2. Kattints az **Integrations** kategóriára.
3. A jobb felső sarokban kattints a három pöttyre (**Custom repositories**).
4. Másold be a repó URL-jét: `https://github.com/karolyia79/smart-grid-yield-simulator`
5. A kategóriánál válaszd az **Integration** opciót, majd kattints az **ADD** gombra.
6. Keresd meg a listában a **Smart Grid Yield Simulator**-t és kattints a **Download** gombra.
7. **FONTOS:** Indítsd újra a Home Assistant-ot a telepítés után!

### 3. Az integráció konfigurálása (UI Setup)
1. Menj a **Settings** -> **Devices & Services** menübe.
2. Kattints az **ADD INTEGRATION** gombra.
3. Keress rá: `Smart Grid Yield Simulator`.
4. A megjelenő ablakban add meg az adatokat:
    * **Fixer.io API Key:** Az általad regisztrált API kulcs.
    * **Nord Pool Sensor:** Válaszd ki a Nord Pool szenzorodat (EUR/MWh).
    * **Inverter Load/Grid Power:** Pillanatnyi Watt (W) értékek.
    * **Daily Import/Export:** Inverter napi kWh számlálói.
    * **Battery SOC:** Akkumulátor töltöttsége százalékban (%).
    * **Battery Capacity & Reserve:** Az akku teljes mérete és a fenntartott tartalék (kWh).

---

## Dashboard Kártya Példa (YAML)

Másold be egy `Manual` kártyába az alábbi kódot. A `#` jellel jelölt sorokat cseréld ki a saját invertered entitásaira!

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
        entity: #sensor.inverter_load_power# # Cseréld: Ház fogyasztás (W)
        name: Ház
        unit: W
        min: 0
        max: 5000
      - type: gauge
        entity: #sensor.inverter_battery_soc# # Cseréld: Akku töltöttség (%)
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
        label: AC forgalom
      - entity: #sensor.inverter_today_energy_import# # Cseréld: Napi import (kWh)
        name: Hálózatról vett
        icon: mdi:transmission-tower-import
      - entity: #sensor.inverter_today_energy_export# # Cseréld: Napi export (kWh)
        name: Hálózatba eladott
        icon: mdi:transmission-tower-export
      - type: section
        label: Akkumulátor & PV
      - entity: #sensor.inverter_today_battery_discharge# # Cseréld: Napi akku kisütés (kWh)
        name: Mai akku használat
        icon: mdi:battery-arrow-down
      - entity: #sensor.inverter_today_production# # Cseréld: Napi napelem termelés (kWh)
        name: Napelem mai össz.
        icon: mdi:solar-power
  - type: entities
    title: Pénzügyi Szimuláció
    show_header_toggle: false
    entities:
      - entity: sensor.tozsdei_tanacsado
        name: Javaslat & Tartalék Infó
        icon: mdi:information-outline
      - entity: sensor.pillanatnyi_megtakaritasi_sebesseg
        name: Pillanatnyi megtakarítás (Ft/h)
        icon: mdi:speedometer
      - type: section
        label: Halmozott Megtakarítás (rezsiárhoz képest)
      - entity: sensor.napi_valos_nyereseg
        name: Ma megtermelt Ft
        icon: mdi:cash-daily
      - entity: sensor.havi_valos_nyereseg
        name: Ebben a hónapban Ft
        icon: mdi:cash-plus
      - entity: sensor.evi_valos_nyereseg
        name: Ebben az évben Ft
        icon: mdi:bank-transfer-in
```

## Kiszámítási képlet
$$\text{Bruttó ár} = \left( \frac{\text{NordPool (EUR/MWh)} \times \text{Fixer árfolyam} \times 1.27}{1000} \right) + 25$$

## Licenc
MIT
