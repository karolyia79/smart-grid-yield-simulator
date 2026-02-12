import logging
import aiohttp
import async_timeout
from datetime import timedelta
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from .const import DOMAIN, PLATFORMS, CONF_FIXER_API_KEY

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    api_key = entry.data[CONF_FIXER_API_KEY]
    
    # Kezdő érték, ha az API nem elérhető
    exchange_data = {"rate": 410.0, "last_update": None}

    async def fetch_fixer_rate():
        """Valuta árfolyam lekérése Fixer.io-ról."""
        url = f"http://data.fixer.io/api/latest?access_key={api_key}&symbols=HUF,EUR"
        try:
            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(15):
                    async with session.get(url) as response:
                        if response.status != 200:
                            _LOGGER.warning("SGY: Fixer.io szerver hiba (Status: %s)", response.status)
                            return exchange_data["rate"]
                            
                        res = await response.json()
                        if res.get("success"):
                            # Fixer.io EUR alapú, így HUF/EUR közvetlenül megkapható
                            rate = float(res["rates"]["HUF"])
                            _LOGGER.info("SGY: Friss árfolyam lekérve: 1 EUR = %s HUF", rate)
                            return rate
                        else:
                            error_info = res.get("error", {}).get("info", "Ismeretlen hiba")
                            _LOGGER.error("SGY: Fixer.io API hiba: %s", error_info)
        except Exception as e:
            _LOGGER.error("SGY: Nem sikerült elérni a Fixer.io-t: %s", e)
        
        return exchange_data["rate"]

    async def async_update_data():
        """Adatok frissítése a Coordinator által."""
        now = hass.time_tracker.async_utcnow()
        
        # Csak 12 óránként frissítjük az árfolyamot, hogy kíméljük az ingyenes API keretet
        if exchange_data["last_update"] is None or now - exchange_data["last_update"] > timedelta(hours=12):
            new_rate = await fetch_fixer_rate()
            exchange_data["rate"] = new_rate
            exchange_data["last_update"] = now

        return {"exchange_rate": exchange_data["rate"]}

    # Coordinator beállítása
    coordinator = DataUpdateCoordinator(
        hass, 
        _LOGGER, 
        name=DOMAIN, 
        update_method=async_update_data, 
        update_interval=timedelta(minutes=30)
    )

    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Integráció eltávolítása."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
