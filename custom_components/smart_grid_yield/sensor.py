import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.const import UnitOfTime
from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        DinamikusArSensor(coordinator, entry),
        ElmeletiNyeresegSensor(coordinator, entry),
        PillanatnyiSebessegSensor(coordinator, entry),
        TozsdeiTanacsadoSensor(coordinator, entry),
        SGYExchangeRateSensor(coordinator, entry),
        SystemLossSensor(coordinator, entry),
        DailyImportCostSensor(coordinator, entry),
        DailyExportRevenueSensor(coordinator, entry)
    ]
    
    acc = IntegrationSensor(integration_method="left", name="SGY Összesített Megtakarítás Számláló", round_digits=2, source_entity="sensor.pillanatnyi_megtakaritasi_sebesseg", unique_id=f"{entry.entry_id}_acc", unit_time=UnitOfTime.HOURS)
    
    meters = [
        UtilityMeterSensor(cron_pattern=None, cycle="daily", name="Napi Valós Nyereség", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_d"),
        UtilityMeterSensor(cron_pattern=None, cycle="monthly", name="Havi Valós Nyereség", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_m"),
        UtilityMeterSensor(cron_pattern=None, cycle="yearly", name="Évi Valós Nyereség", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_y")
    ]
    async_add_entities(entities + [acc] + meters)

class SGYSensorBase(SensorEntity):
    def __init__(self, coordinator, entry):
        self.coordinator, self._entry = coordinator, entry
        self._attr_should_poll = False
    async def async_added_to_hash(self): self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))
    def _get_f(self, key):
        eid = self._entry.data.get(key)
        if not eid: return 0
        s = self.hass.states.get(eid)
        try: return float(s.state) if s and s.state not in ["unknown", "unavailable"] else 0
        except: return 0
    def _get_grid_kw(self):
        mode = self._entry.data.get(CONF_PHASE_SETTING)
        if mode == PHASE_3_INDIVIDUAL:
            return (self._get_f(CONF_GRID_L1) + self._get_f(CONF_GRID_L2) + self._get_f(CONF_GRID_L3)) / 1000
        return self._get_f(CONF_GRID_POWER) / 1000

class DinamikusArSensor(SGYSensorBase):
    _attr_name = "Dinamikus Bruttó Áramár"
    _attr_native_unit_of_measurement = "Ft/kWh"
    _attr_unique_id = "sgy_dynamic_price"
    @property
    def native_value(self):
        tozsde = self._get_f(CONF_SPOT_PRICE)
        rate = self.coordinator.data.get("exchange_rate")
        if not rate: return None
        return round(((tozsde * rate * 1.27) / 1000) + 25.0, 2)

class PillanatnyiSebessegSensor(SGYSensorBase):
    _attr_name = "Pillanatnyi Megtakarítási Sebesség"
    _attr_native_unit_of_measurement = "Ft/h"
    _attr_unique_id = "sgy_saving_speed"
    @property
    def native_value(self):
        load_kw = self._get_f(CONF_LOAD_POWER) / 1000
        grid_kw = self._get_grid_kw()
        price = self.hass.states.get("sensor.dinamikus_brutto_aramar")
        if not price or price.state in ["unknown", "unavailable"]: return round(max(0, load_kw + min(0, grid_kw)) * 70.1, 2)
        p_diff = 70.1 - float(price.state)
        saving = load_kw * 70.1
        return round(saving + (grid_kw * p_diff), 2) if grid_kw > 0 else round(max(0, (load_kw + grid_kw) * 70.1), 2)

class SystemLossSensor(SGYSensorBase):
    _attr_name = "Rendszer pillanatnyi vesztesége"
    _attr_native_unit_of_measurement = "W"
    _attr_unique_id = "sgy_system_loss"
    @property
    def native_value(self):
        pv = self._get_f(CONF_PV_POWER)
        b_in = self._get_f(CONF_BATT_CHARGE)
        b_out = self._get_f(CONF_BATT_DISCHARGE)
        load = self._get_f(CONF_LOAD_POWER)
        grid = self._get_grid_kw() * 1000
        income = pv + b_out + (abs(grid) if grid < 0 else 0)
        usage = load + b_in + (grid if grid > 0 else 0)
        return round(max(0, income - usage), 1)

class TozsdeiTanacsadoSensor(SGYSensorBase):
    _attr_name = "Tőzsdei Tanácsadó"
    _attr_unique_id = "sgy_advisor"
    @property
    def state(self):
        nyer_s = self.hass.states.get("sensor.elmeleti_nyereseg_merteke")
        soc = self._get_f(CONF_BATTERY_SOC)
        if not nyer_s or soc == 0: return "Init..."
        nyer = float(nyer_s.state)
        cap = float(self._entry.data[CONF_BATTERY_CAPACITY])
        res = float(self._entry.data[CONF_BATTERY_RESERVE])
        curr = (cap * soc) / 100
        diff = round(curr - res, 2)
        if curr <= res: return f"STOP 🛑 Tartalék szinten ({round(curr,1)} kWh)"
        if nyer > 15: return f"VÉTEL/TÖLTÉS 🔋 (+{max(0, diff)} kWh szabad)"
        if nyer < -10: return f"ELADÁS/AKKU ⚠️ (+{max(0, diff)} kWh szabad)"
        return f"TARTÁS ⚖️ (+{max(0, diff)} kWh a tartalékig)"

class ElmeletiNyeresegSensor(SGYSensorBase):
    _attr_name = "Elméleti Nyereség mértéke"
    _attr_native_unit_of_measurement = "Ft/kWh"
    _attr_unique_id = "sgy_theo_p"
    @property
    def native_value(self):
        p = self.hass.states.get("sensor.dinamikus_brutto_aramar")
        try: return round(70.1 - float(p.state), 2)
        except: return 0

class DailyImportCostSensor(SGYSensorBase):
    _attr_name = "Napi Hálózati Költség (Tőzsdei)"
    _attr_native_unit_of_measurement = "Ft"
    _attr_unique_id = "sgy_d_imp"
    @property
    def native_value(self):
        kwh = self._get_f(CONF_DAILY_IMPORT)
        p = self.hass.states.get("sensor.dinamikus_brutto_aramar")
        try: return round(kwh * float(p.state), 2)
        except: return 0

class DailyExportRevenueSensor(SGYSensorBase):
    _attr_name = "Napi Hálózati Bevétel (Tőzsdei)"
    _attr_native_unit_of_measurement = "Ft"
    _attr_unique_id = "sgy_d_exp"
    @property
    def native_value(self):
        kwh = self._get_f(CONF_DAILY_EXPORT)
        p = self.hass.states.get("sensor.dinamikus_brutto_aramar")
        try: return round(kwh * float(p.state), 2)
        except: return 0

class SGYExchangeRateSensor(SGYSensorBase):
    _attr_name = "Euro Árfolyam"
    _attr_native_unit_of_measurement = "Ft/EUR"
    _attr_unique_id = "sgy_rate"
    @property
    def native_value(self): return round(self.coordinator.data.get("exchange_rate", 410.0), 2)
