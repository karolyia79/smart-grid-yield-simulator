import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower, UnitOfEnergy
from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Szenzorok beállítása a Config Entry alapján."""
    
    # Itt most már nem a koordinátort, hanem magát az entry-t használjuk
    entities = [
        DinamikusArSensor(entry),
        ElmeletiNyeresegSensor(entry),
        PillanatnyiSebessegSensor(entry),
        TozsdeiTanacsadoSensor(entry),
        SystemLossSensor(entry)
    ]
    
    async_add_entities(entities, update_before_add=True)

class SGYSensorBase(SensorEntity):
    """Alap osztály minden SGY szenzornak."""
    def __init__(self, entry):
        self._entry = entry
        self._attr_has_entity_name = True
        self._attr_should_poll = True # Mivel nincs koordinátor, poll-ozunk
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Smart Grid Yield Simulator",
            "manufacturer": "Károlyi A.",
        }

    def _get_f(self, key):
        """Lebegőpontos érték kinyerése bármilyen entitásból."""
        eid = self._entry.data.get(key)
        if not eid: return 0.0
        s = self.hass.states.get(eid)
        try:
            return float(s.state) if s and s.state not in ["unknown", "unavailable"] else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _calculate_dynamic_price(self):
        """Központosított árszámítás a manuális árfolyam szenzor alapján."""
        tozsde_eur_mwh = self._get_f(CONF_SPOT_PRICE)
        # Az új konstanst használjuk az __init__.py helyett
        rate = self._get_f(CONF_EXCHANGE_RATE_SENSOR)
        if rate <= 0: rate = 410.0 # Alapértelmezett, ha a szenzor nem elérhető
        
        price_huf_kwh = (tozsde_eur_mwh * rate) / 1000
        return round((price_huf_kwh * 1.27) + 25.0, 2)

class DinamikusArSensor(SGYSensorBase):
    _attr_name = "Dinamikus Bruttó Áramár"
    _attr_native_unit_of_measurement = "Ft/kWh"
    
    def __init__(self, entry):
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_dynamic_price"

    @property
    def native_value(self):
        return self._calculate_dynamic_price()

class PillanatnyiSebessegSensor(SGYSensorBase):
    _attr_name = "Pillanatnyi Megtakarítási Sebesség"
    _attr_native_unit_of_measurement = "Ft/h"

    def __init__(self, entry):
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_saving_speed"

    @property
    def native_value(self):
        load_kw = self._get_f(CONF_LOAD_POWER) / 1000
        
        # Fázis mérés logika
        mode = self._entry.data.get(CONF_PHASE_SETTING)
        if mode == PHASE_3_INDIVIDUAL:
            grid_kw = (self._get_f(CONF_GRID_L1) + self._get_f(CONF_GRID_L2) + self._get_f(CONF_GRID_L3)) / 1000
        else:
            grid_kw = self._get_f(CONF_GRID_POWER) / 1000
            
        current_price = self._calculate_dynamic_price()
        if current_price <= 25.0: current_price = 70.1

        p_diff = 70.1 - current_price
        if grid_kw > 0: # Vételezés
            return round((load_kw * 70.1) + (grid_kw * p_diff), 2)
        # Visszatáplálás
        return round(max(0, (load_kw + grid_kw) * 70.1), 2)

class TozsdeiTanacsadoSensor(SGYSensorBase):
    _attr_name = "Tőzsdei Tanácsadó"
    
    def __init__(self, entry):
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_advisor"

    @property
    def native_value(self):
        current_price = self._calculate_dynamic_price()
        nyer = 70.1 - current_price
        soc = self._get_f(CONF_BATTERY_SOC)
        
        if soc < 10: return "TÖLTÉS AJÁNLOTT 🔋"
        if nyer > 15: return "HÁLÓZATI HASZNÁLAT ✅"
        if nyer < -5: return "AKKU ÜZEMMÓD ⚠️"
        return "NORMÁL ÜZEM ⚖️"

class ElmeletiNyeresegSensor(SGYSensorBase):
    _attr_name = "Elméleti Nyereség mértéke"
    _attr_native_unit_of_measurement = "Ft/kWh"

    def __init__(self, entry):
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_theo_p"

    @property
    def native_value(self):
        return round(70.1 - self._calculate_dynamic_price(), 2)

class SystemLossSensor(SGYSensorBase):
    _attr_name = "Rendszer pillanatnyi vesztesége"
    _attr_native_unit_of_measurement = "W"
    
    def __init__(self, entry):
        super().__init__(entry)
        self._attr_unique_id = f"{entry.entry_id}_system_loss"

    @property
    def native_value(self):
        return self._get_f(CONF_TOTAL_LOSS)
