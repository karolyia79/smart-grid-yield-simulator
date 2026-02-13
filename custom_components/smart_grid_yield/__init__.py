import logging
import async_timeout
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .const import DOMAIN, PLATFORMS, CONF_FIXER_API_KEY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api_key = entry.data.get(CONF_FIXER_API_KEY)
    session = async_get_clientsession(hass)

    async def async_update_data():
        if not api_key:
            return {"exchange_rate": 410.0}
        
        url = f"http://data.fixer.io/api/latest?access_key={api_key}&symbols=HUF,EUR"
        try:
            async with async_timeout.timeout(10):
                response = await session.get(url)
                res = await response.json()
                if res.get("success"):
                    return {"exchange_rate": float(res["rates"]["HUF"])}
        except Exception as e:
            _LOGGER.error("SGY: Árfolyam hiba: %s", e)
        return {"exchange_rate": 410.0}

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(hours=12),
    )

    # Nem engedjük, hogy egy hálózati hiba blokkolja a betöltést
    try:
        await coordinator.async_refresh()
    except Exception:
        pass

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
