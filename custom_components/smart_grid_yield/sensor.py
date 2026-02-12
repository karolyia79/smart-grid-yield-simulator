from homeassistant.components.sensor import SensorEntity
from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.const import UnitOfTime
from .const import DOMAIN, CONF_BATTERY_CAPACITY, CONF_BATTERY_RESERVE

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
        UtilityMeterSensor(cron_pattern=None, cycle="daily", name="napi_valos_nyereseg", 
                           source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_daily"),
        UtilityMeterSensor(cron_pattern=None, cycle="monthly", name="havi_valos_nyereseg", 
                           source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_monthly"),
        UtilityMeterSensor(cron_pattern=None, cycle="yearly", name="evi_valos_nyereseg", 
                           source_entity="sensor.osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_yearly"),
    ]

    async_add_entities(entities + [accumulator] + meters)

class DinamikusArSensor(SensorEntity):
    _attr_name = "Dinamikus Bruttó Áramár"
    _attr_native_unit_of_measurement = "Ft/kWh"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_din_ar"
    @property
    def entity_id(self): return "sensor.dinamikus_brutto_aramar"
    @property
    def native_value(self):
        try:
            tozsde_eur = float(self.coordinator.data["spot_price"].state)
            rate = float(self.coordinator.data["exchange_rate"])
            if tozsde_eur > 0:
                return round(((tozsde_eur * rate * 1.27) / 1000) + 25.0, 2)
        except: return None

class DailyImportCostSensor(SensorEntity):
    _attr_name = "Napi Hálózati Költség (Tőzsdei)"
    _attr_native_unit_of_measurement = "Ft"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_daily_imp_cost"
    @property
    def entity_id(self): return "sensor.napi_halozati_koltseg_tozsdei"
    @property
    def native_value(self):
        try:
            kwh = float(self.coordinator.data["daily_import"].state)
            price = float(self.hass.states.get("sensor.dinamikus_brutto_aramar").state)
            return round(kwh * price, 2)
        except: return 0

class DailyExportRevenueSensor(SensorEntity):
    _attr_name = "Napi Hálózati Bevétel (Tőzsdei)"
    _attr_native_unit_of_measurement = "Ft"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_daily_exp_rev"
    @property
    def entity_id(self): return "sensor.napi_halozati_bevetel_tozsdei"
    @property
    def native_value(self):
        try:
            kwh = float(self.coordinator.data["daily_export"].state)
            price = float(self.hass.states.get("sensor.dinamikus_brutto_aramar").state)
            return round(kwh * price, 2)
        except: return 0

class ElmeletiNyeresegSensor(SensorEntity):
    _attr_name = "Elméleti Nyereség mértéke"
    _attr_native_unit_of_measurement = "Ft/kWh"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_elm_nyer"
    @property
    def entity_id(self): return "sensor.elmeleti_nyereseg_merteke"
    @property
    def native_value(self):
        try:
            din = float(self.hass.states.get("sensor.dinamikus_brutto_aramar").state)
            return round(70.1 - din, 2)
        except: return 0

class PillanatnyiSebessegSensor(SensorEntity):
    _attr_name = "Pillanatnyi Megtakarítási Sebesség"
    _attr_native_unit_of_measurement = "Ft"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_pill_seb"
    @property
    def entity_id(self): return "sensor.pillanatnyi_megtakaritasi_sebesseg"
    @property
    def native_value(self):
        try:
            load = float(self.coordinator.data["load_power"].state) / 1000
            grid = float(self.coordinator.data["grid_power"].state) / 1000
            if grid <= 0: return round(load * 70.1, 4)
            nyer = float(self.hass.states.get("sensor.elmeleti_nyereseg_merteke").state)
            return round(((load - grid) * 70.1) + (grid * nyer if nyer > 0 else 0), 4)
        except: return 0

class TozsdeiTanacsadoSensor(SensorEntity):
    _attr_name = "Tőzsdei Tanácsadó"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_adv"
        self._capacity = entry.data.get(CONF_BATTERY_CAPACITY, 10.0)
        self._reserve_kwh = entry.data.get(CONF_BATTERY_RESERVE, 2.0)
    @property
    def entity_id(self): return "sensor.tozsdei_tanacsado"
    @property
    def state(self):
        try:
            nyer = float(self.hass.states.get("sensor.elmeleti_nyereseg_merteke").state)
            usable = round(self._capacity - self._reserve_kwh, 1)
            if nyer > 15: return "VÉTEL ÉS TÖLTÉS 🔋 (Extrém olcsó!)"
            if nyer > 0: return "VÉTEL ✅ (Olcsóbb mint a rezsi)"
            if nyer < -10: return f"ELADÁS / AKKU ⚠️ ({usable} kWh felett!)"
            return "TARTÁS ⚖️ (Napelem/Fix rezsi)"
        except: return "Init..."

class SGYExchangeRateSensor(SensorEntity):
    _attr_name = "Euro Arfolyam"
    _attr_native_unit_of_measurement = "Ft/EUR"
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._attr_unique_id = f"{entry.entry_id}_ex_r"
    @property
    def entity_id(self): return "sensor.euro_arfolyam"
    @property
    def native_value(self):
        return round(self.coordinator.data["exchange_rate"], 2)
