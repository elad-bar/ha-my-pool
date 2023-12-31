from abc import ABC
import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ICON, Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .common.base_entity import BaseEntity, async_setup_entities
from .common.consts import (
    ACTION_ENTITY_TURN_OFF,
    ACTION_ENTITY_TURN_ON,
    ATTR_ATTRIBUTES,
    ATTR_IS_ON,
    SIGNAL_DEVICE_NEW,
)
from .common.entity_descriptions import IntegrationBinarySensorEntityDescription
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
            Platform.SWITCH,
            device_id,
            IntegrationSwitchEntity,
            async_add_entities,
        )

    entry.async_on_unload(
        async_dispatcher_connect(hass, SIGNAL_DEVICE_NEW, _async_device_new)
    )


class IntegrationSwitchEntity(BaseEntity, SwitchEntity, ABC):
    """Representation of a sensor."""

    def __init__(
        self,
        entity_description: IntegrationBinarySensorEntityDescription,
        coordinator: Coordinator,
        device_id: int,
    ):
        super().__init__(entity_description, coordinator, device_id)

        self._attr_device_class = entity_description.device_class

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.async_execute_device_action(ACTION_ENTITY_TURN_ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.async_execute_device_action(ACTION_ENTITY_TURN_OFF)

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
