import logging
import aiohttp
import async_timeout
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from .const import DOMAIN, PLATFORMS, CONF_SPOT_PRICE, CONF_LOAD_POWER, CONF_GRID_POWER, CONF_FIXER_API_KEY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api_key = entry.data[CONF_FIXER_API_KEY]
    exchange_data = {"rate": 410.0, "last_update": None}

    async def fetch_fixer_rate():
        url = f"http://data.fixer.io/api/latest?access_key={api_key}&symbols=HUF,EUR"
        try:
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        res = await response.json()
                        if res.get("success"):
                            rate = float(res["rates"]["HUF"] / res["rates"]["EUR"])
                            _LOGGER.info("SGY: Arfolyam frissitve: %s Ft/EUR", rate)
                            return rate
        except Exception as e:
            _LOGGER.error("SGY: Fixer hiba: %s", e)
        return exchange_data["rate"]

    async def async_update_data():
        now = hass.time_tracker.async_utcnow()
        if exchange_data["last_update"] is None or now - exchange_data["last_update"] > timedelta(hours=8):
            exchange_data["rate"] = await fetch_fixer_rate()
            exchange_data["last_update"] = now

        return {
            "spot_price": hass.states.get(entry.data[CONF_SPOT_PRICE]),
            "load_power": hass.states.get(entry.data[CONF_LOAD_POWER]),
            "grid_power": hass.states.get(entry.data[CONF_GRID_POWER]),
            "exchange_rate": exchange_data["rate"],
        }

    coordinator = DataUpdateCoordinator(
        hass, _LOGGER, name=DOMAIN,
        update_method=async_update_data,
        update_interval=timedelta(seconds=30),
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
