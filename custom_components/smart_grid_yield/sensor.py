import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.integration.sensor import IntegrationSensor
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.const import UnitOfTime
from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Szenzorok beállítása."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    
    # Alapszenzorok példányosítása
    entities = [
        DinamikusArSensor(coordinator, entry),
        ElmeletiNyeresegSensor(coordinator, entry),
        PillanatnyiSebessegSensor(coordinator, entry),
        TozsdeiTanacsadoSensor(coordinator, entry),
        SGYExchangeRateSensor(coordinator, entry),
        SystemLossSensor(coordinator, entry)
    ]
    
    # Először adjuk hozzá az alap szenzorokat, hogy létezzenek a rendszerben
    async_add_entities(entities)

    # Az integrálót és a mérőket külön adjuk hozzá, mert ezek függnek a fenti sebesség szenzortól
    # Megjegyzés: A source_entity-nek a pontos entitás ID-t kell megadni. 
    # Ha a domain 'smart_grid_yield', az ID valószínűleg 'sensor.pillanatnyi_megtakaritasi_sebesseg' lesz.
    
    acc = IntegrationSensor(
        integration_method="left", 
        name="SGY Összesített Megtakarítás Számláló", 
        round_digits=2, 
        source_entity="sensor.pillanatnyi_megtakaritasi_sebesseg", 
        unique_id=f"{entry.entry_id}_acc", 
        unit_time=UnitOfTime.HOURS
    )
    
    meters = [
        UtilityMeterSensor(cron_pattern=None, cycle="daily", name="Napi Valós Nyereség", source_entity="sensor.sgy_osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_d"),
        UtilityMeterSensor(cron_pattern=None, cycle="monthly", name="Havi Valós Nyereség", source_entity="sensor.sgy_osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_m"),
        UtilityMeterSensor(cron_pattern=None, cycle="yearly", name="Évi Valós Nyereség", source_entity="sensor.sgy_osszesitett_megtakaritas_szamlalo", unique_id=f"{entry.entry_id}_y")
    ]
    
    async_add_entities([acc] + meters)

class SGYSensorBase(SensorEntity):
    """Alap osztály minden SGY szenzornak."""
    def __init__(self, coordinator, entry):
        self.coordinator = coordinator
        self._entry = entry
        self._attr_should_poll = False
        # Dinamikus név beállítása az ütközések elkerülésére
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "SGY Simulator",
            "manufacturer": "Károlyi A.",
        }

    async def async_added_to_hash(self):
        """Amikor hozzáadjuk a HA-hoz."""
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    def _get_f(self, key):
        """Segédfüggvény lebegőpontos érték kinyeréséhez egy entitásból."""
        eid = self._entry.data.get(key)
        if not eid: return 0.0
        s = self.hass.states.get(eid)
        try:
            return float(s.state) if s and s.state not in ["unknown", "unavailable"] else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _get_grid_kw(self):
        """Hálózati teljesítmény kW-ban a konfiguráció alapján."""
        mode = self._entry.data.get(CONF_PHASE_SETTING)
        if mode == PHASE_3_INDIVIDUAL:
            return (self._get_f(CONF_GRID_L1) + self._get_f(CONF_GRID_L2) + self._get_f(CONF_GRID_L3)) / 1000
        return self._get_f(CONF_GRID_POWER) / 1000

    def _calculate_dynamic_price(self):
        """Központosított árszámítás a szenzorok közötti konzisztenciához."""
        tozsde_eur_mwh = self._get_f(CONF_SPOT_PRICE)
        rate = self.coordinator.data.get("exchange_rate", 410.0)
        price_huf_kwh = (tozsde_eur_mwh * rate) / 1000
        return round((price_huf_kwh * 1.27) + 25.0, 2)

class DinamikusArSensor(SGYSensorBase):
    _attr_name = "Dinamikus Bruttó Áramár"
    _attr_native_unit_of_measurement = "Ft/kWh"
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_dynamic_price"

    @property
    def native_value(self):
        return self._calculate_dynamic_price()

class PillanatnyiSebessegSensor(SGYSensorBase):
    _attr_name = "Pillanatnyi Megtakarítási Sebesség"
    _attr_native_unit_of_measurement = "Ft/h"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_saving_speed"

    @property
    def native_value(self):
        load_kw = self._get_f(CONF_LOAD_POWER) / 1000
        grid_kw = self._get_grid_kw()
        current_price = self._calculate_dynamic_price()
        
        # Ha az árszámítás hibás, használjunk alapértelmezett rezsiárat
        if current_price <= 25.0: # Csak az RHD van meg
            current_price = 70.1

        p_diff = 70.1 - current_price
        if grid_kw > 0:
            return round((load_kw * 70.1) + (grid_kw * p_diff), 2)
        return round(max(0, (load_kw + grid_kw) * 70.1), 2)

class SystemLossSensor(SGYSensorBase):
    _attr_name = "Rendszer pillanatnyi vesztesége"
    _attr_native_unit_of_measurement = "W"
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_system_loss"

    @property
    def native_value(self):
        return self._get_f(CONF_TOTAL_LOSS)

class TozsdeiTanacsadoSensor(SGYSensorBase):
    _attr_name = "Tőzsdei Tanácsadó"
    
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_advisor"

    @property
    def state(self):
        current_price = self._calculate_dynamic_price()
        nyer = round(70.1 - current_price, 2)
        soc = self._get_f(CONF_BATTERY_SOC)
        
        cap = float(self._entry.data.get(CONF_BATTERY_CAPACITY, 10.0))
        res = float(self._entry.data.get(CONF_BATTERY_RESERVE, 2.0))
        curr = (cap * soc) / 100
        diff = round(curr - res, 2)
        
        if curr <= res: return f"STOP 🛑 Tartalék szinten ({round(curr,1)} kWh)"
        if nyer > 15: return f"VÉTEL/TÖLTÉS 🔋 (+{max(0, diff)} kWh szabad)"
        if nyer < -10: return f"ELADÁS/AKKU ⚠️ (+{max(0, diff)} kWh szabad)"
        return f"TARTÁS ⚖️ (+{max(0, diff)} kWh a tartalékig)"

class ElmeletiNyeresegSensor(SGYSensorBase):
    _attr_name = "Elméleti Nyereség mértéke"
    _attr_native_unit_of_measurement = "Ft/kWh"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_theo_p"

    @property
    def native_value(self):
        current_price = self._calculate_dynamic_price()
        return round(70.1 - current_price, 2)

class SGYExchangeRateSensor(SGYSensorBase):
    _attr_name = "Euro Árfolyam"
    _attr_native_unit_of_measurement = "Ft/EUR"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_rate"

    @property
    def native_value(self): 
        return round(self.coordinator.data.get("exchange_rate", 410.0), 2)
