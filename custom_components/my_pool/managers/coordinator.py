from copy import copy
import logging
import sys
from typing import Any, Callable

from homeassistant.components.sensor import SensorDeviceClass
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
    CONFIG_TECHNICIAN_POOL_SIZE,
    DATA_ITEM_CONFIG,
    DATA_ITEM_DEVICES,
    DATA_ITEM_MEMBER_DETAILS,
    DOMAIN,
    MANUFACTURER,
    MAXIMUM_SALINITY_PPM,
    MINIMUM_SALINITY_PPM,
    NORMAL_SALINITY_PPM_RANGE,
    PREFERRED_SALINITY_PPM,
    PRODUCT_PAGE,
    PRODUCT_URL,
    RUNTIME_DEVICE_ON,
    RUNTIME_DEVICE_TURBO,
    RUNTIME_DEVICE_TURBO_TIME,
    RUNTIME_SALINITY_VALUE,
    SALINITY_STATUS,
    SALT_MISSING,
    SALT_WEIGHT_FOR_PREFERRED_SALINITY,
    UNIT_PH,
    UPDATE_API,
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
    _data_retrievers: dict[Platform, Callable[[int, int, Any], dict]] | None
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
            update_interval=UPDATE_API,
            update_method=self._async_update_data,
        )

        self._config_manager = config_manager

        self._api = RestAPI(hass, config_manager)
        self._entity_descriptions = None
        self._data_retrievers = None

    @property
    def api(self) -> RestAPI:
        return self._api

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
        self._load_data_retrievers()
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
        entity_description,
        device_id: int,
        action_key: str,
    ) -> Callable:
        device_data = self.get_data(device_id, entity_description)
        actions = device_data.get(ATTR_ACTIONS)
        async_action = actions.get(action_key)

        return async_action

    def _load_data_retrievers(self):
        data_retrievers = {
            Platform.SENSOR: self._sensor_state_handler,
            Platform.SELECT: self._select_state_handler,
            Platform.BINARY_SENSOR: self._binary_sensor_state_handler,
            Platform.SWITCH: self._switch_state_handler,
            Platform.NUMBER: self._number_state_handler,
        }

        self._data_retrievers = data_retrievers

    def _sensor_state_handler(
        self, device_id: int | None, state: int, entity_description
    ):
        if entity_description.device_class == SensorDeviceClass.TEMPERATURE:
            state_str = str(state)
            state_str_fixed = f"{state_str[:2]}.{state_str[2:].ljust(2, '0')}"
            state = float(state_str_fixed)

        elif entity_description.device_class == SensorDeviceClass.SIGNAL_STRENGTH:
            state = (state / 2) - 110

        elif entity_description.native_unit_of_measurement == UNIT_PH:
            state_str = str(state)
            state_str_fixed = f"{state_str[:1]}.{state_str[1:].ljust(2, '0')}"
            state = float(state_str_fixed)

        elif entity_description.key == SALT_MISSING:
            device_data = self._api.get_device_data(device_id)
            data = device_data.get("data")

            pool_size = data.get(CONFIG_TECHNICIAN_POOL_SIZE)
            current_salinity = data.get(RUNTIME_SALINITY_VALUE)

            state = self._get_missing_salt(pool_size, current_salinity)

        elif entity_description.key == SALINITY_STATUS:
            device_data = self._api.get_device_data(device_id)
            data = device_data.get("data")

            current_salinity = data.get(RUNTIME_SALINITY_VALUE)

            state = self._get_salinity_status(current_salinity)

        result = {ATTR_STATE: state}

        return result

    def _select_state_handler(self, _device_id: int, state: int, _entity_description):
        result = {
            ATTR_STATE: state,
            ATTR_ACTIONS: {ACTION_ENTITY_SELECT_OPTION: self._handle_select_action},
        }

        return result

    def _binary_sensor_state_handler(
        self, _device_id: int, state: int, entity_description
    ):
        on_value = entity_description.on_value
        is_on = str(on_value).lower() == str(state).lower()

        result = {ATTR_IS_ON: is_on}

        return result

    def _switch_state_handler(self, _device_id: int, state: int, entity_description):
        on_value = entity_description.on_value
        is_on = str(on_value).lower() == str(state).lower()

        result = {
            ATTR_IS_ON: is_on,
            ATTR_ACTIONS: {
                ACTION_ENTITY_TURN_ON: self._handle_turn_on_action,
                ACTION_ENTITY_TURN_OFF: self._handle_turn_off_action,
            },
        }

        return result

    def _number_state_handler(self, _device_id: int, state: int, entity_description):
        if entity_description.native_unit_of_measurement == UNIT_PH:
            state_str = str(state)
            state_str_fixed = f"{state_str[:1]}.{state_str[1:].ljust(2, '0')}"
            state = float(state_str_fixed)

        result = {
            ATTR_STATE: state,
            ATTR_ACTIONS: {
                ACTION_ENTITY_SET_NATIVE_VALUE: self._handle_set_number_action
            },
        }

        return result

    def get_data(self, device_id: int, entity_description) -> dict | None:
        try:
            device_data = self._api.get_device_data(device_id)
            data = device_data.get("data")

            state = data.get(entity_description.key)

            data_retriever = self._data_retrievers.get(
                entity_description.platform, Platform.SENSOR
            )

            result = data_retriever(device_id, state, entity_description)

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

            if ed.platform not in entity_descriptions:
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
        await self._handle_turn_x_action(device_id, entity_description, True)

    async def _handle_turn_off_action(
        self, device_id: int, entity_description: IntegrationEntityDescription
    ):
        await self._handle_turn_x_action(device_id, entity_description, False)

    async def _handle_turn_x_action(
        self,
        device_id: int,
        entity_description: IntegrationEntityDescription,
        value: bool,
    ):
        value_int = 1 if value else 0

        if entity_description.key in [RUNTIME_DEVICE_ON]:
            turbo_data = self.get_data(device_id, RUNTIME_DEVICE_TURBO)
            turbo_time_data = self.get_data(device_id, RUNTIME_DEVICE_TURBO_TIME)

            turbo = turbo_data.get(ATTR_STATE)
            turbo_time = turbo_time_data.get(ATTR_STATE)

            request_data = {"state": value_int, "turbo": turbo, "turboTime": turbo_time}

            await self._api.set_direct_request(device_id, "DeviceAction", request_data)

        else:
            await self._api.set_value(device_id, entity_description.key, value_int)

    async def _handle_set_number_action(
        self,
        device_id: int,
        entity_description: IntegrationEntityDescription,
        value: int,
    ):
        await self._api.set_value(device_id, entity_description.key, value)

    @staticmethod
    def _get_missing_salt(pool_size, salinity) -> float:
        required_salt = pool_size * SALT_WEIGHT_FOR_PREFERRED_SALINITY
        salinity_gap = 1 - (salinity / PREFERRED_SALINITY_PPM)
        missing_salt = salinity_gap * required_salt
        missing_salt_str = f"{missing_salt:.3f}"
        result = float(missing_salt_str)

        return result

    @staticmethod
    def _get_salinity_status(salinity) -> str | None:
        status = None
        normal_range_minimum = NORMAL_SALINITY_PPM_RANGE[0]
        normal_range_maximum = NORMAL_SALINITY_PPM_RANGE[1]

        if normal_range_minimum <= salinity <= normal_range_maximum:
            status = "ok"

        elif MAXIMUM_SALINITY_PPM >= salinity >= normal_range_minimum:
            status = "normal_high"

        elif normal_range_maximum >= salinity >= MINIMUM_SALINITY_PPM:
            status = "normal_low"

        elif salinity > MAXIMUM_SALINITY_PPM:
            status = "very_high"

        elif salinity < MINIMUM_SALINITY_PPM:
            status = "very_low"

        return status
