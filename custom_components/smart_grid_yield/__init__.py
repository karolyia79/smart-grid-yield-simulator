async def async_update_data():
    now = hass.time_tracker.async_utcnow()
    if exchange_data["last_update"] is None or now - exchange_data["last_update"] > timedelta(hours=8):
        exchange_data["rate"] = await fetch_fixer_rate()
        exchange_data["last_update"] = now

    return {
        "spot_price": hass.states.get(entry.data[CONF_SPOT_PRICE]),
        "load_power": hass.states.get(entry.data[CONF_LOAD_POWER]),
        "grid_power": hass.states.get(entry.data[CONF_GRID_POWER]),
        "daily_import": hass.states.get(entry.data[CONF_DAILY_IMPORT]),
        "daily_export": hass.states.get(entry.data[CONF_DAILY_EXPORT]),
        "exchange_rate": exchange_data["rate"],
    }
