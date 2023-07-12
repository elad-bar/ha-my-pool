"""Platform for climate integration."""
import logging
import sys
from asyncio import sleep
from copy import copy

from aiohttp import ClientResponseError, ClientSession
from homeassistant.const import CONF_PASSWORD, CONF_EMAIL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .config_manager import ConfigManager
from ..common.consts import API_MAX_ATTEMPTS, CONF_FCM_TOKEN, SIGNAL_DEVICE_NEW
from ..common.endpoints import Endpoints
from ..common.exceptions import InvalidTokenError, LoginError, OperationFailedException

_LOGGER = logging.getLogger(__name__)


class RestAPI:
    _devices: dict
    _member_details: dict | None

    _session: ClientSession | None
    _config_manager: ConfigManager
    _hass: HomeAssistant | None
    _dispatched_devices: list[int]

    _api_status: bool

    def __init__(
        self, hass: HomeAssistant | None, config_manager: ConfigManager
    ):
        """Initialize the climate entity."""

        self._devices = {}
        self._member_details = None

        self._session = None

        self._hass = hass
        self._config_manager = config_manager

        self._dispatched_devices = []

    @property
    def member_details(self):
        result = self._member_details

        return result

    @property
    def devices(self):
        result = self._devices

        return result

    async def initialize(self, throw_error: bool = False):
        try:
            if self._session is None:
                if self._hass is None:
                    self._session = ClientSession()
                else:
                    self._session = async_create_clientsession(hass=self._hass)

                await self._connect()

        except LoginError as lex:
            if throw_error:
                raise lex

            else:
                _LOGGER.error(
                    "Failed to login, Please update credentials and try again"
                )

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.warning(
                f"Failed to initialize session, Error: {ex}, Line: {line_number}"
            )

    async def terminate(self):
        if self._hass is None:
            await self._session.close()

    async def update(self):
        """Fetch new state parameters for the sensor."""
        await self._internal_update()

    async def _connect(self):
        await self._validate_token()

        if self._config_manager.token is None:
            await self._login()

    async def _validate_token(self):
        try:
            token = self._config_manager.token

            if token is not None:
                validation_response = await self._get_request(Endpoints.CheckToken)

                await self._handle_auth(validation_response, token)

        except Exception as ex:
            _LOGGER.error(f"Failed to check token, Error: {ex}")

    async def _login(self):
        request_data = {
            CONF_EMAIL: self._config_manager.username,
            CONF_PASSWORD: self._config_manager.password,
            CONF_FCM_TOKEN: ""
        }

        try:
            login_response = await self._post_request(Endpoints.Login, request_data)

            await self._handle_auth(login_response)

        except Exception as ex:
            await self._config_manager.update_token_key(None)

            _LOGGER.error(f"Failed to login, Error: {ex}")

        if self._config_manager.token is None:
            raise LoginError()

    async def _handle_auth(self, response: dict, token: str | None = None):
        member_details = None
        devices = []

        success = response.get("success", False)
        message = response.get("message", "Check token")

        _LOGGER.debug(f"{message} [Success: {success}]")

        if success:
            data = response.get("data")

            devices: list = data.get("ownedDevices")
            shared_devices: list = data.get("devices")
            devices.extend(shared_devices)

            member_details = data.get("member")

            if token is None:
                token = response.get("token")

        self._member_details = member_details
        self._devices = {
            device.get("id"): {
                "metadata": device,
                "data": None
            }
            for device in devices
        }

        await self._config_manager.update_token_key(token)

    async def _internal_update(self, attempt: int = 1):
        """Fetch new state parameters for the sensor."""
        error = None
        line_number = None

        try:
            await self._connect()

            for device_id in self._devices:
                await self._update_device(device_id)

        except LoginError as lex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            await self._config_manager.update_token_key(None)

            error = lex

        except InvalidTokenError as itex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            await self._config_manager.update_token_key(None)

            error = itex

        except Exception as ex:
            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            error = ex

        if error is not None:
            if attempt < API_MAX_ATTEMPTS:
                _LOGGER.debug(
                    f"Failed to update (Attempt #{attempt}), trying again, "
                    f"Error: {error}, "
                    f"Line: {line_number}"
                )

                await sleep(1)

                await self._internal_update(attempt + 1)

            else:
                _LOGGER.error(
                    f"Failed to update (Attempt #{attempt}), Error: {error}, Line: {line_number}"
                )

    async def _update_device(self, device_id: int):
        _LOGGER.debug(f"Starting to update device: {device_id}")

        try:
            new_device = device_id not in self._dispatched_devices

            await self._fetch_data(device_id)

            if new_device:
                self._dispatched_devices.append(device_id)

                if self._hass is not None:
                    async_dispatcher_send(
                        self._hass,
                        SIGNAL_DEVICE_NEW,
                        self._config_manager.entry_id,
                        device_id,
                    )

        except ClientResponseError as cre:
            if cre.status in [401, 403]:
                raise InvalidTokenError(f"Update device: {device_id}")

            else:
                raise cre

    async def _perform_action(
        self, request_data: dict, operation: str, attempt: int = 1
    ):
        try:
            error_msg = "Not implemented"

            if error_msg != "Success":
                raise OperationFailedException(operation, request_data, error_msg)

        except ClientResponseError as cre:
            if cre.status in [401, 403]:
                await self._config_manager.update_token_key(None)

                if attempt < API_MAX_ATTEMPTS:
                    await self._connect()

                    await self._perform_action(request_data, operation, attempt + 1)

                else:
                    raise InvalidTokenError(f"Perform action, Data: {request_data}")

            else:
                raise cre

    async def _fetch_data(self, device_id: int):
        request_data = {
            "_deviceId": device_id
        }

        response = await self._get_request(Endpoints.DeviceStatus, request_data)
        success = response.get("success", False)

        if success:
            data = response.get("data")

            self._devices[device_id]["data"] = data

        else:
            self._devices[device_id]["data"] = None

    async def _post_request(
        self, endpoint: Endpoints, data: dict | list | None = None
    ) -> dict | None:
        url = f"{Endpoints.BaseURL}{endpoint}"

        headers = None
        if endpoint != Endpoints.Login:
            headers = {
                "Authorization": f"Bearer {self._config_manager.token}",
            }

        async with self._session.post(url, headers=headers, json=data, ssl=False) as response:
            response.raise_for_status()

            result = await response.json()
            _LOGGER.debug(f"Request to {url}, Body: {data}, Result: {result}")

        return result

    async def _get_request(
        self,
        endpoint: Endpoints,
        data: dict | None = None
    ) -> dict | None:

        query_string = ""

        if data is not None:
            params = [f"{key}={data[key]}" for key in data]

            query_string_params = "&".join(params)

            query_string = f"?{query_string_params}"

        url = f"{Endpoints.BaseURL}{endpoint}{query_string}"

        headers = {
            "Authorization": f"Bearer {self._config_manager.token}",
        }

        async with self._session.get(url, headers=headers, ssl=False) as response:
            response.raise_for_status()

            result = await response.json()
            _LOGGER.debug(f"Request to {url}, Body: {data}, Result: {result}")

        return result

    def get_device_data(self, device_id: int) -> dict | None:
        device_data = copy(self._devices.get(device_id))

        return device_data
