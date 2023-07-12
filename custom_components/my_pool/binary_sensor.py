import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .managers.coordinator import Coordinator
from .common.base_entity import async_setup_entities, BaseEntity
from .common.consts import ATTR_ATTRIBUTES, ATTR_IS_ON, SIGNAL_DEVICE_NEW
from .common.entity_descriptions import IntegrationBinarySensorEntityDescription

_LOGGER = logging.getLogger(__name__)

CURRENT_DOMAIN = Platform.BINARY_SENSOR


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    @callback
    def _async_device_new(entry_id: str, device_id: int):
        if entry.entry_id != entry_id:
            return

        async_setup_entities(
            hass,
            entry,
            CURRENT_DOMAIN,
            device_id,
            IntegrationBinarySensorEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class IntegrationBinarySensorEntity(BaseEntity, BinarySensorEntity):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: IntegrationBinarySensorEntityDescription,
        coordinator: Coordinator,
    ):
        super().__init__(entity_description, coordinator, CURRENT_DOMAIN)

        self._attr_device_class = entity_description.device_class

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            is_on = data.get(ATTR_IS_ON)
            attributes = data.get(ATTR_ATTRIBUTES)
            icon = data.get(ATTR_ICON)

            self._attr_is_on = is_on
            self._attr_extra_state_attributes = attributes

            if icon is not None:
                self._attr_icon = icon

        else:
            self._attr_is_on = None
