import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integráció beállítása a Config Entry alapján."""
    
    # Mivel nincs szükségünk külső API-ra, nem kell Coordinator.
    # Az adatokat a sensor.py fogja közvetlenül a megadott szenzorokból kiolvasni.
    
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = entry.data

    # A sensor platform elindítása
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integráció eltávolítása."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok
