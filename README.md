# Smart Grid Yield Simulator (SGY) 🇭🇺



Ez egy Home Assistant egyedi integráció, ami egy kifejezetten a magyarországi napelemes (hibrid vagy szigetüzemű) rendszerekhez készült hobby projekt. Az integráció segít kiszámolni a valós pénzügyi megtakarítást a dinamikus tőzsdei áramárak és a rögzített rezsiárak (70.1 Ft/kWh) összevetésével.

## 🚀 Főbb funkciók

* **Dinamikus Árkezelés:** A Nord Pool EUR/MWh adatait a Fixer.io árfolyamán azonnal Ft/kWh-ra konvertálja.
* **Regionális Optimalizáció:** Mivel a Nord Pool jelenleg nem közöl natív magyar árakat, a rendszer az **osztrák (AT)** piaci adatokat használja, amely a piaci összefonódás miatt reprezentatív a magyar viszonyokra is.
* **Intelligens Tőzsdei Tanácsadó:** Javaslatot tesz az akkumulátor használatára a beállított **biztonsági tartalék (kWh)** szint figyelembevételével.
* **Inverter Hatékonyság:** Az inverter saját belső veszteség-szenzorának (W) támogatása.

---

## 🛠️ Szükséges entitások a beüzemeléshez

### 1. Előfeltételek és Nord Pool konfiguráció
Az integráció telepítése előtt győződj meg róla, hogy a **Nord Pool** integrációban az **osztrák régiót** állítottad be:
* **Region:** `AT`
* **Currency:** `EUR`

### 2. Árfolyam figyelés (Kötelező beállítás!)
Az integráció működéséhez szükséged van egy aktuális EUR/HUF árfolyam szenzorra. Ezt a `configuration.yaml` fájlba kell manuálisan beillesztened. 

**FIGYELEM:** Az `access_key=` után a saját, [fixer.io](https://fixer.io/) oldalon regisztrált API kulcsodat írd be! A `scan_interval` értékét (8 óra) ne csökkentsd, mert az ingyenes Fixer.io csomag korlátozott számú lekérdezést engedélyez.

```yaml
sensor:
  - platform: rest
    name: "Euro Arfolyam"
    # CSERÉLD KI AZ ALÁBBI KULCSOT A SAJÁTADRA:
    resource: "http://data.fixer.io/api/latest?access_key=IDE_IRD_A_SAJAT_API_KULCSODAT&symbols=HUF,EUR"
    value_template: "{{ (value_json.rates.HUF / value_json.rates.EUR) | round(2) }}"
    unit_of_measurement: "Ft/EUR"
    scan_interval: 28800 # 8 óránként (Ne állítsd kisebbre az ingyenes verziólimit miatt!)
    force_update: true
```

---

## 🛠️ Az Integráció telepítése

Válassz az alábbi két módszer közül a telepítéshez:

### **"A" módszer: HACS használatával (Ajánlott)**
1. Nyisd meg a **HACS** felületét a Home Assistantban.
2. Kattints a jobb felső sarokban a **három pontra** (menü), majd válaszd a **Custom repositories** opciót.
3. Másold be ennek a repónak az URL-jét a *Repository* mezőbe. (https://github.com/karolyia79/smart-grid-yield-simulator)
4. A *Category* listából válaszd ki az **Integration** opciót, majd kattints az **Add** gombra.
5. Keresd meg a listában megjelenő **Smart Grid Yield Simulator**-t, és kattints a **Download** gombra.
6. **Fontos:** Indítsd újra a Home Assistant-ot!



### **"B" módszer: Manuális telepítés**
1. Töltsd le a forráskódot (**ZIP** formátumban vagy `git clone` használatával).
2. Keresd meg a `custom_components` mappát a Home Assistant konfigurációs könyvtáradban (ahol a `configuration.yaml` is található).
3. Másold be ide a `smart_grid_yield` mappát az összes tartalmával együtt.
4. **Fontos:** Indítsd újra a Home Assistant-ot!

---

### ⚙️ Konfigurálás a felhasználói felületen

Miután újraindult a rendszer, az integrációt aktiválnod kell a felületen:

1. Menj a **Beállítások** -> **Eszközök és szolgáltatások** menüpontba.
2. Kattints az **Integráció hozzáadása** gombra a jobb alsó sarokban.
3. Keress rá a listában: **Smart Grid Yield Simulator**.
4. A megjelenő ablakban add meg a kért adatokat:
    * Fázisok száma és mérési mód.
    * Nord Pool szenzor kiválasztása.
    * Fogyasztásmérő és egyéb technikai szenzorok társítása.
  
---

### Konfigurációs táblázat

| Kategória | Mező | Leírás |
| :--- | :--- | :--- |
| **Pénzügy** | Fixer.io API Key | Az EUR/HUF váltáshoz szükséges API kulcs. |
| **Tőzsde** | Nord Pool Spot Price | Az osztrák (AT) régióra állított EUR/MWh szenzor. |
| **Fogyasztás** | Household Load (W) | A ház aktuális pillanatnyi fogyasztása (W). |
| **Hálózat** | Grid Power (W) | Hálózati teljesítmény (1 vagy 3 fázis konfiguráció szerint). |
| **Energia** | Daily Import/Export (kWh) | Napi hálózati forgalom számlálók. |
| **Akku** | Battery SOC (%) | Az akkumulátor aktuális töltöttsége. |
| **Veszteség** | Inverter Loss (W) | Az inverter belső veszteség-szenzora. |

---

## 📊 Létrehozott entitások (Kimenetek)

A telepítés után az integráció az alábbi szenzorokat hozza létre automatikusan:

| Szenzor neve | Entitás azonosító | Leírás |
| :--- | :--- | :--- |
| **Dinamikus Bruttó Áramár** | `sensor.dinamikus_brutto_aramar` | Aktuális piaci ár Ft/kWh-ban (ÁFA + RHD). |
| **Megtakarítási Sebesség** | `sensor.pillanatnyi_megtakaritasi_sebesseg` | Pillanatnyi pénzügyi hozam Ft/óra egységben. |
| **Tőzsdei Tanácsadó** | `sensor.tozsdei_tanacsado` | Szöveges javaslat és akku tartalék információ. |
| **Elméleti Nyereség** | `sensor.elmeleti_nyereseg_merteke` | A 70.1 Ft és a piaci ár aktuális különbsége. |
| **Napi Valós Nyereség** | `sensor.napi_valos_nyereseg` | Ma elért összes megtakarítás Ft-ban. |
| **Havi Valós Nyereség** | `sensor.havi_valos_nyereseg` | Aktuális havi megtakarítás Ft-ban. |
| **Inverter Veszteség** | `sensor.rendszer_pillanatnyi_vesztesege` | Az inverter által jelentett pillanatnyi veszteség (W). |
| **Euro Árfolyam** | `sensor.euro_arfolyam` | A Fixer.io-tól lekért aktuális HUF/EUR váltószám. |

---

## 🧮 Matematikai alapok és számítási metodika

A rendszer célja, hogy az osztrák tőzsdei nyers adatból egy olyan bruttó végfelhasználói árat képezzen, amely összehasonlítható a magyarországi lakossági rezsiárral.



### 1. Bruttó áramár számítása (Ft/kWh)
$$\text{Bruttó ár} = \left( \frac{\text{NordPool (AT)}_{EUR/MWh} \times \text{Fixer}_{HUF/EUR}}{1000} \times 1.27 \right) + 25$$

* **Osztrák árak:** Mivel a magyar (HUPX) és az osztrák (EXAA/NordPool AT) árak korrelációja rendkívül magas, a számítás alapja az osztrák piaci ár.
* **Deviza váltás:** EUR/MWh -> HUF/MWh (Fixer.io árfolyam).
* **Mértékegység váltás:** HUF/MWh -> HUF/kWh (osztás 1000-rel).
* **Adók és Díjak:** 27% ÁFA és 25 Ft/kWh fix Rendszerhasználati Díj.

### 2. Pillanatnyi megtakarítás (Ft/h)
A megtakarítási sebesség számítása figyelembe veszi a napelem által kiváltott vásárlást és az esetleges hálózati exportot is:
* **Önfogyasztás:** Minden kWh, amit nem a hálózatból veszünk meg, **70.1 Ft** megtakarítást termel.
* **Export:** Ha a piaci ár alacsonyabb mint 70.1 Ft, az exportált energia értéke a rezsiár és a piaci ár különbségeként jelenik meg a szimulációban.

---

## 📱 Dashboard kártya minta (YAML)

Másold be egy `Manual` kártyába a Home Assistant dashboardon. 
**FIGYELEM:** A `#` jelek közötti részeket manuálisan kell átírnod a saját entitásaid neveire!

```yaml
type: vertical-stack
cards:
  - type: horizontal-stack
    cards:
      - type: gauge
        entity: sensor.dinamikus_brutto_aramar # Az integráció hozza létre
        name: Bruttó Ár
        min: 0
        max: 120
        severity: {green: 0, yellow: 60, red: 70.1}
        needle: true
      - type: gauge
        # === MANUÁLISAN CSERÉLD KI: A ház fogyasztás szenzorodra ===
        entity: #sensor.haz_pillanatnyi_fogyasztas# 
        name: Ház
        unit: W
        min: 0
        max: 5000
      - type: gauge
        # === MANUÁLISAN CSERÉLD KI: Az akkumulátor töltöttség szenzorodra ===
        entity: #sensor.akku_soc_szazalek# 
        name: Akku
        unit: "%"
        min: 0
        max: 100
        severity: {red: 0, yellow: 20, green: 45}
        needle: true
  - type: entities
    title: Mai Energia Forgalom
    show_header_toggle: false
    entities:
      - type: section
        label: Pillanatnyi Hálózat (W)
      # === MANUÁLISAN CSERÉLD KI: A hálózati mérőd (Smart Meter) wattos szenzorára ===
      - entity: #sensor.halozati_teljesitmeny_osszesen# 
        name: Hálózat összesen
      - type: section
        label: Napi Statisztika (kWh)
      # === MANUÁLISAN CSERÉLD KI: A napi hálózati import (vétel) szenzorodra ===
      - entity: #sensor.napi_halozati_import# 
        name: Hálózatról vett
      # === MANUÁLISAN CSERÉLD KI: A napi hálózati export (eladás) szenzorodra ===
      - entity: #sensor.napi_halozati_export# 
        name: Hálózatba eladott
      # === MANUÁLISAN CSERÉLD KI: A napi napelem termelés szenzorodra ===
      - entity: #sensor.napelem_napi_termeles# 
        name: Napelem mai termelés
      - entity: sensor.rendszer_pillanatnyi_vesztesege # Az integráció hozza létre
        name: Inverter belső veszteség
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

---

## 📄 Licenc / License

Ez a projekt az **MIT Licenc** alatt áll. / This project is licensed under the **MIT License**.

### Magyar nyelvű összefoglaló (nem helyettesíti az eredeti licencet):
A szoftver szabadon felhasználható, másolható és módosítható, az alábbi feltételekkel:
* Az eredeti szerzői jogi nyilatkozatot és a licenc szövegét minden másolatban fel kell tüntetni.
* **Felelősségkizárás:** A szoftverért semmilyen garanciát nem vállalok. A használatból eredő esetleges károkért (pl. hibás számítások, rendszerleállás) a fejlesztő nem vonható felelősségre. Mindenki saját felelősségére használja!

---
### English Summary:
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, provided that the copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
