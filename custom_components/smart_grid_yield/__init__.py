import logging
import async_timeout
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import dt as dt_util

from .const import DOMAIN, PLATFORMS, CONF_FIXER_API_KEY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integráció beállítása config entry alapján."""
    api_key = entry.data.get(CONF_FIXER_API_KEY)
    
    # Központi session használata
    session = async_get_clientsession(hass)

    async def fetch_fixer_rate():
        """Valutaárfolyam letöltése."""
        if not api_key:
            return 410.0
            
        url = f"http://data.fixer.io/api/latest?access_key={api_key}&symbols=HUF,EUR"
        try:
            async with async_timeout.timeout(10):
                response = await session.get(url)
                if response.status == 200:
                    res = await response.json()
                    if res.get("success"):
                        rate = float(res["rates"]["HUF"])
                        _LOGGER.debug("SGY: Új árfolyam letöltve: %s", rate)
                        return rate
                _LOGGER.warning("SGY: Fixer.io hiba (status: %s)", response.status)
        except Exception as e:
            _LOGGER.error("SGY: Nem sikerült az árfolyam frissítése: %s", e)
        
        return 410.0 # Alapértelmezett érték hiba esetén

    async def async_update_data():
        """Coordinator adatfrissítés."""
        # Az utolsó frissítést a Coordinator saját maga kezeli az update_interval-lal, 
        # nem kell manuálisan nézni az időt, hacsak nem akarsz spórolni az API hívással.
        rate = await fetch_fixer_rate()
        return {"exchange_rate": rate}

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(hours=12), # Elég 12 óránként frissíteni az árfolyamot
    )

    # Az első frissítés megpróbálása
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Platformok (sensor.py stb.) elindítása
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integráció eltávolítása."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
