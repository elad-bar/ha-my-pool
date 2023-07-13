from abc import ABC
import logging

from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_STATE, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import BaseEntity, async_setup_entities
from .common.consts import (
    ACTION_ENTITY_SET_NATIVE_VALUE,
    ATTR_ATTRIBUTES,
    SIGNAL_DEVICE_NEW,
)
from .common.entity_descriptions import IntegrationNumberEntityDescription
from .managers.coordinator import Coordinator

_LOGGER = logging.getLogger(__name__)


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
            Platform.NUMBER,
            device_id,
            IntegrationNumberEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class IntegrationNumberEntity(BaseEntity, NumberEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: IntegrationNumberEntityDescription,
        coordinator: Coordinator,
        device_id: int,
    ):
        super().__init__(entity_description, coordinator, device_id)

        self._attr_native_min_value = entity_description.native_min_value
        self._attr_native_max_value = entity_description.native_max_value

    async def async_set_native_value(self, value: float) -> None:
        """Change the selected option."""
        await self.async_execute_device_action(ACTION_ENTITY_SET_NATIVE_VALUE, value)

    def update_component(self, data):
        """Fetch new state parameters for the sensor."""
        if data is not None:
            state = data.get(ATTR_STATE)
            attributes = data.get(ATTR_ATTRIBUTES)

            self._attr_native_value = state
            self._attr_extra_state_attributes = attributes

        else:
            self._attr_native_value = None
