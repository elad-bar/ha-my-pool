from copy import copy
from datetime import timedelta
import logging
import sys
from typing import Callable

from homeassistant.const import ATTR_STATE, Platform
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import slugify

from ..common.consts import (
    ACTION_ENTITY_SELECT_OPTION,
    ACTION_ENTITY_SET_NATIVE_VALUE,
    ACTION_ENTITY_TURN_OFF,
    ACTION_ENTITY_TURN_ON,
    ATTR_ACTIONS,
    ATTR_IS_ON,
    DATA_ITEM_CONFIG,
    DATA_ITEM_DEVICES,
    DATA_ITEM_MEMBER_DETAILS,
    DOMAIN,
    MANUFACTURER,
    PRODUCT_PAGE,
    PRODUCT_URL,
)
from ..common.entity_descriptions import (
    DEFAULT_ENTITY_DESCRIPTIONS,
    IntegrationEntityDescription,
)
from .config_manager import ConfigManager
from .rest_api import RestAPI

_LOGGER = logging.getLogger(__name__)


class Coordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    _entity_descriptions: dict[Platform, list[EntityDescription]] | None
    _api: RestAPI | None
    _config_manager: ConfigManager

    def __init__(
        self,
        hass,
        config_manager: ConfigManager,
    ):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=config_manager.name,
            update_interval=timedelta(seconds=30),
            update_method=self._async_update_data,
        )

        self._config_manager = config_manager

        self._api = None
        self._entity_descriptions = None

    @property
    def config_manager(self):
        return self._config_manager

    @property
    def devices(self):
        return self._api.devices

    @property
    def member_details(self):
        return self._api.member_details

    @property
    def platforms(self) -> list[Platform]:
        return list(self._entity_descriptions.keys())

    @property
    def config_data(self):
        return self._config_manager.data

    def get_entity_descriptions(self, platform: Platform):
        entity_descriptions = self._entity_descriptions.get(platform)

        return entity_descriptions

    def get_device(self, device_id: int) -> DeviceInfo:
        device_data = self._api.get_device_data(device_id)
        metadata = device_data.get("metadata")

        nick_name = metadata.get("nickname")
        serial_number = metadata.get("serialNumber")

        device_type = metadata.get("deviceType")
        version = metadata.get("firmware-main-current")

        product_page = PRODUCT_PAGE.get(device_type, "")
        product_url = f"{PRODUCT_URL}{product_page}"

        device_name = serial_number if nick_name is None else nick_name

        device_info = DeviceInfo(
            identifiers={(DOMAIN, str(device_id))},
            name=device_name,
            manufacturer=MANUFACTURER,
            model=device_type,
            hw_version=version,
            configuration_url=product_url,
        )

        return device_info

    async def initialize(self):
        self._load_entity_descriptions()

        await self._api.initialize()

    async def _async_update_data(self):
        """Fetch parameters from API endpoint.

        This is the place to pre-process the parameters to lookup tables
        so entities can quickly look up their parameters.
        """
        try:
            await self._api.update()

            return {
                DATA_ITEM_DEVICES: self._api.devices,
                DATA_ITEM_MEMBER_DETAILS: self._api.member_details,
                DATA_ITEM_CONFIG: self.config_data,
            }

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    def get_device_action(
        self,
        entity_description: IntegrationEntityDescription,
        device_id: int,
        action_key: str,
    ) -> Callable:
        device_data = self.get_data(device_id, entity_description)
        actions = device_data.get(ATTR_ACTIONS)
        async_action = actions.get(action_key)

        return async_action

    def get_data(self, device_id: int, entity_description) -> dict | None:
        try:
            device_data = self._api.get_device_data(device_id)
            data = device_data.get("data")

            state = data.get(entity_description.key)

            result = {}

            if entity_description.platform in [Platform.BINARY_SENSOR, Platform.SWITCH]:
                on_value = entity_description.on_value
                is_on = on_value == state

                result[ATTR_IS_ON] = is_on

            else:
                result[ATTR_STATE] = state

            if entity_description.platform in [Platform.SELECT]:
                result[ATTR_ACTIONS] = {
                    ACTION_ENTITY_SELECT_OPTION: self._handle_select_action
                }

            elif entity_description.platform in [Platform.SWITCH]:
                result[ATTR_ACTIONS] = {
                    ACTION_ENTITY_TURN_ON: self._handle_turn_on_action,
                    ACTION_ENTITY_TURN_OFF: self._handle_turn_off_action,
                }

            elif entity_description.platform in [Platform.NUMBER]:
                result[ATTR_ACTIONS] = {
                    ACTION_ENTITY_SET_NATIVE_VALUE: self._handle_set_number_action
                }

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to extract data for {entity_description}, Error: {ex}, Line: {line_number}"
            )

            result = None

        return result

    def _load_entity_descriptions(self):
        entity_descriptions = {}

        for entity_description in DEFAULT_ENTITY_DESCRIPTIONS:
            ed = copy(entity_description)
            ed.translation_key = slugify(ed.key)

            if ed.platform not in entity_description:
                entity_descriptions[ed.platform] = []

            entity_descriptions[ed.platform].append(ed)

        self._entity_descriptions = entity_descriptions

    async def _handle_select_action(
        self,
        device_id: int,
        entity_description: IntegrationEntityDescription,
        option: str,
    ):
        value = int(option)

        await self._api.set_value(device_id, entity_description.key, value)

    async def _handle_turn_on_action(
        self, device_id: int, entity_description: IntegrationEntityDescription
    ):
        await self._api.set_value(device_id, entity_description.key, 1)

    async def _handle_turn_off_action(
        self, device_id: int, entity_description: IntegrationEntityDescription
    ):
        await self._api.set_value(device_id, entity_description.key, 0)

    async def _handle_set_number_action(
        self,
        device_id: int,
        entity_description: IntegrationEntityDescription,
        intensity: int,
    ):
        await self._api.set_value(device_id, entity_description.key, intensity)
