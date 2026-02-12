import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.const import UnitOfTime
from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Alap szenzorok
    entities = [
        DinamikusArSensor(coordinator, entry),
        ElmeletiNyeresegSensor(coordinator, entry),
        PillanatnyiSebessegSensor(coordinator, entry),
        TozsdeiTanacsadoSensor(coordinator, entry),
        SGYExchangeRateSensor(coordinator, entry),
        DailyImportCostSensor(coordinator, entry),
        DailyExportRevenueSensor(coordinator, entry)
    ]

    # Riemann-összeg mérő a megtakarítási sebességből (Ft/h -> Ft)
    acc = IntegrationSensor(
        integration_method="left",
        name="SGY Összesített Megtakarítás Számláló",
        round_digits=2,
        source_entity="sensor.pillanatnyi_megtakaritasi_sebesseg",
        unique_id=f"{entry.entry_id}_acc",
        unit_time=UnitOfTime.HOURS,
    )

    # Időszakos mérők (Napi, Havi, Éves)
    meters = [
        UtilityMeterSensor(cron_pattern=None, cycle="daily", name="Napi Valós Nyereség", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_d"),
        UtilityMeterSensor(cron_pattern=None, cycle="monthly", name="Havi Valós Nyereség", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_m"),
        UtilityMeterSensor(cron_pattern=None, cycle="yearly", name="Évi Valós Nyereség", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_y"),
    ]

    async_add_entities(entities + [acc] + meters)

class SGYSensorBase(SensorEntity):
    """Alap osztály a közös funkcióknak."""
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
        self._attr_should_poll = False

    async def async_added_to_hash(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    def _get_state(self, entity_id):
        state = self.hass.states.get(entity_id)
        if state is None or state.state in ["unknown", "unavailable"]:
            return None
        try:
            return float(state.state)
        except ValueError:
            return None

class DinamikusArSensor(SGYSensorBase):
    _attr_name = "Dinamikus Bruttó Áramár"
    _attr_native_unit_of_measurement = "Ft/kWh"
    _attr_unique_id = "sgy_dynamic_price"

    @property
    def native_value(self):
        tozsde = self._get_state(self._entry.data[CONF_SPOT_PRICE])
        rate = self.coordinator.data.get("exchange_rate")
        if tozsde is None or rate is None:
            return None
        # Bruttó ár: (EUR/MWh * rate * 1.27 / 1000) + RHD (25 Ft)
        return round(((tozsde * rate * 1.27) / 1000) + 25.0, 2)

class PillanatnyiSebessegSensor(SGYSensorBase):
    _attr_name = "Pillanatnyi Megtakarítási Sebesség"
    _attr_native_unit_of_measurement = "Ft/h"
    _attr_unique_id = "sgy_saving_speed"

    @property
    def native_value(self):
        load = self._get_state(self._entry.data[CONF_LOAD_POWER])
        if load is None: return 0
        load_kw = load / 1000

        mode = self._entry.data.get(CONF_PHASE_SETTING)
        if mode == PHASE_3_INDIVIDUAL:
            l1 = self._get_state(self._entry.data[CONF_GRID_L1]) or 0
            l2 = self._get_state(self._entry.data[CONF_GRID_L2]) or 0
            l3 = self._get_state(self._entry.data[CONF_GRID_L3]) or 0
            grid_kw = (l1 + l2 + l3) / 1000
        else:
            grid = self._get_state(self._entry.data[CONF_GRID_POWER]) or 0
            grid_kw = grid / 1000

        # Logika: 
        # Ha grid_kw > 0: Eladás van. Megtakarítás = (Ház fogyasztás * rezsiár) + (Export * (rezsiár - tőzsdei ár))
        # Ha grid_kw <= 0: Import van. Megtakarítás = (Napelem által fedezett rész * rezsiár)
        # Egyszerűsítve: Rezsiáron spórolunk mindent, amit nem a hálózatból veszünk.
        
        dynamic_price = self.hass.states.get("sensor.dinamikus_brutto_aramar")
        if dynamic_price is None or dynamic_price.state in ["unknown", "unavailable"]:
            return round(max(0, load_kw - max(0, -grid_kw)) * 70.1, 2)

        p_diff = 70.1 - float(dynamic_price.state)
        
        # Alap megtakarítás a ház saját fogyasztásán
        saving = load_kw * 70.1
        
        # Ha exportálunk (grid_kw > 0), az exportált rész profitja/vesztesége a tőzsdéhez képest
        if grid_kw > 0:
            return round(saving + (grid_kw * p_diff), 2)
        else:
            # Ha importálunk (grid_kw < 0), akkor csak a nem hálózati rész spórol rezsiáron
            actual_saving = (load_kw + grid_kw) * 70.1 # grid_kw itt negatív!
            return round(max(0, actual_saving), 2)

class TozsdeiTanacsadoSensor(SGYSensorBase):
    _attr_name = "Tőzsdei Tanácsadó"
    _attr_unique_id = "sgy_advisor"

    @property
    def state(self):
        nyer_state = self.hass.states.get("sensor.elmeleti_nyereseg_merteke")
        soc = self._get_state(self._entry.data[CONF_BATTERY_SOC])
        
        if nyer_state is None or soc is None: return "Adatokra vár..."
        
        nyer = float(nyer_state.state)
        cap = float(self._entry.data[CONF_BATTERY_CAPACITY])
        res = float(self._entry.data[CONF_BATTERY_RESERVE])
        
        curr_kwh = (cap * soc) / 100
        diff = round(curr_kwh - res, 2)

        if curr_kwh <= res:
            return f"STOP 🛑 Tartalék szinten ({round(curr_kwh,1)} kWh)"
        
        if nyer > 15:
            return f"VÉTEL/TÖLTÉS 🔋 (+{max(0, diff)} kWh szabad)"
        elif nyer < -10:
            return f"ELADÁS/AKKU ⚠️ (+{max(0, diff)} kWh szabad)"
        
        return f"TARTÁS ⚖️ (+{max(0, diff)} kWh a tartalékig)"

class ElmeletiNyeresegSensor(SGYSensorBase):
    _attr_name = "Elméleti Nyereség mértéke"
    _attr_native_unit_of_measurement = "Ft/kWh"
    _attr_unique_id = "sgy_theoretical_profit"

    @property
    def native_value(self):
        price = self.hass.states.get("sensor.dinamikus_brutto_aramar")
        if price is None or price.state in ["unknown", "unavailable"]: return 0
        return round(70.1 - float(price.state), 2)

class DailyImportCostSensor(SGYSensorBase):
    _attr_name = "Napi Hálózati Költség (Tőzsdei)"
    _attr_native_unit_of_measurement = "Ft"
    _attr_unique_id = "sgy_daily_import_cost"

    @property
    def native_value(self):
        kwh = self._get_state(self._entry.data[CONF_DAILY_IMPORT])
        price = self.hass.states.get("sensor.dinamikus_brutto_aramar")
        if kwh is None or price is None or price.state in ["unknown", "unavailable"]: return 0
        return round(kwh * float(price.state), 2)

class DailyExportRevenueSensor(SGYSensorBase):
    _attr_name = "Napi Hálózati Bevétel (Tőzsdei)"
    _attr_native_unit_of_measurement = "Ft"
    _attr_unique_id = "sgy_daily_export_revenue"

    @property
    def native_value(self):
        kwh = self._get_state(self._entry.data[CONF_DAILY_EXPORT])
        price = self.hass.states.get("sensor.dinamikus_brutto_aramar")
        if kwh is None or price is None or price.state in ["unknown", "unavailable"]: return 0
        return round(kwh * float(price.state), 2)

class SGYExchangeRateSensor(SGYSensorBase):
    _attr_name = "Euro Árfolyam"
    _attr_native_unit_of_measurement = "Ft/EUR"
    _attr_unique_id = "sgy_exchange_rate"

    @property
    def native_value(self):
        return round(self.coordinator.data.get("exchange_rate", 410.0), 2)
