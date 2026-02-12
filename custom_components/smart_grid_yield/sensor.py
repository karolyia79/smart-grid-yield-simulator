from homeassistant.components.sensor import SensorEntity
from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.const import UnitOfTime
from .const import DOMAIN, CONF_BATTERY_CAPACITY, CONF_BATTERY_RESERVE, CONF_BATTERY_SOC, CONF_SPOT_PRICE, CONF_LOAD_POWER, CONF_GRID_POWER, CONF_DAILY_IMPORT, CONF_DAILY_EXPORT

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        DinamikusArSensor(coordinator, entry),
        ElmeletiNyeresegSensor(coordinator, entry),
        PillanatnyiSebessegSensor(coordinator, entry),
        TozsdeiTanacsadoSensor(coordinator, entry),
        SGYExchangeRateSensor(coordinator, entry),
        DailyImportCostSensor(coordinator, entry),
        DailyExportRevenueSensor(coordinator, entry)
    ]

    accumulator = IntegrationSensor(
        integration_method="left",
        name="osszesitett_megtakaritas_szamlalo",
        round_digits=2,
        source_entity="sensor.pillanatnyi_megtakaritasi_sebesseg",
        unique_id=f"{entry.entry_id}_accumulator",
        unit_time=UnitOfTime.HOURS,
    )

    meters = [
        UtilityMeterSensor(cron_pattern=None, cycle="daily", name="napi_valos_nyereseg", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_daily"),
        UtilityMeterSensor(cron_pattern=None, cycle="monthly", name="havi_valos_nyereseg", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_monthly"),
        UtilityMeterSensor(cron_pattern=None, cycle="yearly", name="evi_valos_nyereseg", source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_yearly"),
    ]

    async_add_entities(entities + [accumulator] + meters)

class DinamikusArSensor(SensorEntity):
    _attr_name = "Dinamikus Bruttó Áramár"
    _attr_native_unit_of_measurement = "Ft/kWh"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
    @property
    def entity_id(self): return "sensor.dinamikus_brutto_aramar"
    @property
    def native_value(self):
        try:
            tozsde_eur = float(self.hass.states.get(self._entry.data[CONF_SPOT_PRICE]).state)
            rate = float(self.coordinator.data["exchange_rate"])
            return round(((tozsde_eur * rate * 1.27) / 1000) + 25.0, 2)
        except: return None

class TozsdeiTanacsadoSensor(SensorEntity):
    _attr_name = "Tőzsdei Tanácsadó"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
    @property
    def entity_id(self): return "sensor.tozsdei_tanacsado"
    @property
    def state(self):
        try:
            nyer = float(self.hass.states.get("sensor.elmeleti_nyereseg_merteke").state)
            soc = float(self.hass.states.get(self._entry.data[CONF_BATTERY_SOC]).state)
            cap = float(self._entry.data[CONF_BATTERY_CAPACITY])
            res = float(self._entry.data[CONF_BATTERY_RESERVE])
            
            curr_kwh = (cap * soc) / 100
            diff = round(curr_kwh - res, 2)

            if curr_kwh <= res: return f"STOP 🛑 Tartalék szinten ({curr_kwh} kWh)"
            if nyer > 15: return f"VÉTEL/TÖLTÉS 🔋 (+{max(0, diff)} kWh szabad)"
            if nyer < -10: return f"ELADÁS/AKKU ⚠️ (+{max(0, diff)} kWh szabad)"
            return f"TARTÁS ⚖️ (+{max(0, diff)} kWh a tartalékig)"
        except: return "Számítás..."

class PillanatnyiSebessegSensor(SensorEntity):
    _attr_name = "Pillanatnyi Megtakarítási Sebesség"
    _attr_native_unit_of_measurement = "Ft/h"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
    @property
    def entity_id(self): return "sensor.pillanatnyi_megtakaritasi_sebesseg"
    @property
    def native_value(self):
        try:
            load = float(self.hass.states.get(self._entry.data[CONF_LOAD_POWER]).state) / 1000
            grid = float(self.hass.states.get(self._entry.data[CONF_GRID_POWER]).state) / 1000
            if grid <= 0: return round(load * 70.1, 2)
            nyer = float(self.hass.states.get("sensor.elmeleti_nyereseg_merteke").state)
            return round(((load - grid) * 70.1) + (grid * nyer if nyer > 0 else 0), 2)
        except: return 0

class ElmeletiNyeresegSensor(SensorEntity):
    _attr_name = "Elméleti Nyereség mértéke"
    _attr_native_unit_of_measurement = "Ft/kWh"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
    @property
    def entity_id(self): return "sensor.elmeleti_nyereseg_merteke"
    @property
    def native_value(self):
        try:
            din = float(self.hass.states.get("sensor.dinamikus_brutto_aramar").state)
            return round(70.1 - din, 2)
        except: return 0

class DailyImportCostSensor(SensorEntity):
    _attr_name = "Napi Hálózati Költség (Tőzsdei)"
    _attr_native_unit_of_measurement = "Ft"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
    @property
    def entity_id(self): return "sensor.napi_halozati_koltseg_tozsdei"
    @property
    def native_value(self):
        try:
            kwh = float(self.hass.states.get(self._entry.data[CONF_DAILY_IMPORT]).state)
            price = float(self.hass.states.get("sensor.dinamikus_brutto_aramar").state)
            return round(kwh * price, 2)
        except: return 0

class DailyExportRevenueSensor(SensorEntity):
    _attr_name = "Napi Hálózati Bevétel (Tőzsdei)"
    _attr_native_unit_of_measurement = "Ft"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
    @property
    def entity_id(self): return "sensor.napi_halozati_bevetel_tozsdei"
    @property
    def native_value(self):
        try:
            kwh = float(self.hass.states.get(self._entry.data[CONF_DAILY_EXPORT]).state)
            price = float(self.hass.states.get("sensor.dinamikus_brutto_aramar").state)
            return round(kwh * price, 2)
        except: return 0

class SGYExchangeRateSensor(SensorEntity):
    _attr_name = "Euro Arfolyam"
    _attr_native_unit_of_measurement = "Ft/EUR"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
    @property
    def entity_id(self): return "sensor.euro_arfolyam"
    @property
    def native_value(self):
        return round(self.coordinator.data["exchange_rate"], 2)
