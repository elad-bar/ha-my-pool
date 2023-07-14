import logging
import sys
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from ..managers.coordinator import Coordinator
from .consts import DOMAIN
from .entity_descriptions import IntegrationEntityDescription

_LOGGER = logging.getLogger(__name__)


def async_setup_entities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    platform: Platform,
    device_id: int,
    entity_type: type,
    async_add_entities,
):
    try:
        coordinator = hass.data[DOMAIN][entry.entry_id]

        entities = []

        entity_descriptions = coordinator.get_entity_descriptions(platform)

        for entity_description in entity_descriptions:
            entity = entity_type(entity_description, coordinator, device_id)

            entities.append(entity)

        _LOGGER.debug(f"Setting up {platform} entities: {entities}")

        async_add_entities(entities, True)

    except Exception as ex:
        exc_type, exc_obj, tb = sys.exc_info()
        line_number = tb.tb_lineno

        _LOGGER.error(
            f"Failed to initialize {platform}, Error: {ex}, Line: {line_number}"
        )


class BaseEntity(CoordinatorEntity):
    _device_id: int
    _entity_description: IntegrationEntityDescription
    _translations: dict

    def __init__(
        self,
        entity_description: IntegrationEntityDescription,
        coordinator: Coordinator,
        device_id: int,
    ):
        super().__init__(coordinator)

        self._entity_description = entity_description
        self.entity_description = entity_description

        device_info = coordinator.get_device(device_id)
        identifiers = device_info.get("identifiers")
        serial_number = list(identifiers)[0][1]

        entity_name = coordinator.config_manager.get_entity_name(
            entity_description, device_info
        )

        unique_id = slugify(
            f"{entity_description.platform}_{serial_number}_{entity_description.key}"
        )

        self._attr_device_info = device_info
        self._attr_name = entity_name
        self._attr_unique_id = unique_id

        self._data = {}
        self._device_id = device_id

    @property
    def _local_coordinator(self) -> Coordinator:
        return self.coordinator

    @property
    def data(self) -> dict | None:
        return self._data

    async def async_execute_device_action(self, key: str, *kwargs: Any):
        async_device_action = self._local_coordinator.get_device_action(
            self._entity_description, self._device_id, key
        )

        await async_device_action(key, self.entity_description, *kwargs)

        await self.coordinator.async_request_refresh()

    def update_component(self, data):
        pass

    def _handle_coordinator_update(self) -> None:
        """Fetch new state parameters for the sensor."""
        try:
            new_data = self._local_coordinator.get_data(
                self._device_id, self.entity_description
            )

            if self._data != new_data:
                _LOGGER.debug(f"Data for {self.unique_id}: {new_data}")

                self.update_component(new_data)

                self._data = new_data

                self.async_write_ha_state()

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to update {self.unique_id}, Error: {ex}, Line: {line_number}"
            )
