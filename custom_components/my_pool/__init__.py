import logging
import sys

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .common.consts import DOMAIN, DEFAULT_NAME
from .common.exceptions import LoginError
from .managers.rest_api import RestAPI
from .managers.config_manager import ConfigManager
from .managers.coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(_hass, _config):
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Shinobi Video component."""
    initialized = False

    try:
        config_manager = ConfigManager(hass, entry)
        await config_manager.initialize()

        is_initialized = config_manager.is_initialized

        if is_initialized:
            coordinator = Coordinator(hass, config_manager)
            await coordinator.initialize()

            hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

            await hass.config_entries.async_forward_entry_setups(entry, coordinator.platforms)

            _LOGGER.info(
                f"Start loading {DOMAIN} integration, Entry ID: {entry.entry_id}"
            )

            await coordinator.async_config_entry_first_refresh()

            _LOGGER.info("Finished loading integration")

        initialized = is_initialized

    except LoginError:
        _LOGGER.info(f"Failed to login {DEFAULT_NAME} API, cannot log integration")

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(
            f"Failed to load {DEFAULT_NAME}, error: {ex}, line: {line_number}"
        )

    return initialized


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading {DOMAIN} integration, Entry ID: {entry.entry_id}")

    coordinator: Coordinator = hass.data[DOMAIN][entry.entry_id]

    platforms = coordinator.platforms

    for platform in platforms:
        await hass.config_entries.async_forward_entry_unload(entry, platform)

    del hass.data[DOMAIN][entry.entry_id]

    return True
