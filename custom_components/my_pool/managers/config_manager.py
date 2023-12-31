import json
import logging
import sys

from cryptography.fernet import Fernet, InvalidToken

from homeassistant.config_entries import STORAGE_VERSION, ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import translation
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.json import JSONEncoder
from homeassistant.helpers.storage import Store
from homeassistant.util import slugify

from ..common.consts import (
    CONFIGURATION_FILE,
    DEFAULT_NAME,
    DOMAIN,
    STORAGE_DATA_KEY,
    STORAGE_DATA_TOKEN_KEY,
)
from ..common.entity_descriptions import IntegrationEntityDescription

_LOGGER = logging.getLogger(__name__)


class ConfigManager:
    _encryption_key: str | None
    _crypto: Fernet | None
    _data: dict | None

    _store: Store | None
    _store_data: dict | None
    _entry_data: dict | None
    _password: str | None
    _entry_title: str
    _entry_id: str

    _is_set_up_mode: bool
    _is_initialized: bool

    def __init__(self, hass: HomeAssistant | None, entry: ConfigEntry | None = None):
        self._hass = hass
        self._entry = entry

        self._encryption_key = None
        self._crypto = None

        self._data = None

        self._password = None

        self._store = None
        self._entry_data = None
        self._store_data = None
        self._translations = None

        self._is_set_up_mode = entry is None
        self._is_initialized = False

        if self._is_set_up_mode:
            self._entry_data = {}
            self._entry_title = DEFAULT_NAME
            self._entry_id = "config"

        else:
            self._entry_data = entry.data
            self._entry_title = entry.title
            self._entry_id = entry.entry_id

        if hass is not None:
            self._store = Store(
                hass, STORAGE_VERSION, CONFIGURATION_FILE, encoder=JSONEncoder
            )

    @property
    def is_initialized(self) -> bool:
        is_initialized = self._is_initialized

        return is_initialized

    @property
    def data(self):
        return self._data

    @property
    def entry(self):
        entry = self._entry

        return entry

    @property
    def entry_id(self):
        entry_id = self._entry_id

        return entry_id

    @property
    def name(self):
        entry_title = self._entry_title

        return entry_title

    @property
    def username(self) -> str:
        username = self.data.get(CONF_USERNAME)

        return username

    @property
    def password_hashed(self) -> str:
        password_hashed = self._encrypt(self.password)

        return password_hashed

    @property
    def password(self) -> str:
        password = self._data.get(CONF_PASSWORD)

        return password

    @property
    def token(self) -> str | None:
        key = self._data.get(STORAGE_DATA_TOKEN_KEY)

        return key

    async def initialize(self):
        try:
            await self._load()

            password = self._entry_data.get(CONF_PASSWORD)

            if not self._is_set_up_mode:
                password = self._decrypt(password)

            self._data[CONF_USERNAME] = self._entry_data.get(CONF_USERNAME)
            self._data[CONF_PASSWORD] = password

            self._translations = await translation.async_get_translations(
                self._hass, self._hass.config.language, "entity", {DOMAIN}
            )

            _LOGGER.debug(
                f"Translations loaded, Data: {json.dumps(self._translations)}"
            )

            self._is_initialized = True

        except InvalidToken:
            self._is_initialized = False

            _LOGGER.error("Invalid encryption key")

        except Exception as ex:
            self._is_initialized = False

            exc_type, exc_obj, tb = sys.exc_info()
            line_number = tb.tb_lineno

            _LOGGER.error(
                f"Failed to initialize configuration manager, Error: {ex}, Line: {line_number}"
            )

    def get_entity_name(
        self, entity_description: IntegrationEntityDescription, device_info: DeviceInfo
    ) -> str:
        entity_key = slugify(entity_description.key)
        platform = entity_description.platform

        device_name = device_info.get("name")

        translation_key = f"component.{DOMAIN}.entity.{platform}.{entity_key}.name"

        translated_name = self._translations.get(
            translation_key, entity_description.name
        )

        _LOGGER.debug(
            f"Translations requested '{device_name}', Key: {translation_key}, "
            f"Entity: {entity_description.name}, Value: {translated_name}"
        )

        entity_name = (
            device_name
            if translated_name is None or translated_name == ""
            else f"{device_name} {translated_name}"
        )

        return entity_name

    def update_credentials(self, data: dict):
        self._entry_data = data

    async def update_token_key(self, key: str | None):
        self._data[STORAGE_DATA_TOKEN_KEY] = key

        await self._save()

    async def _load(self):
        self._data = None

        await self._load_config_from_file()
        await self._load_encryption_key()

        if self._data is None:
            self._data = {STORAGE_DATA_TOKEN_KEY: None}

            await self._save()

    async def _load_config_from_file(self):
        if self._store is not None:
            self._store_data = await self._store.async_load()

            if self._store_data is not None:
                self._data = self._store_data.get(self._entry_id)

    async def _load_encryption_key(self):
        if self._store_data is not None:
            if STORAGE_DATA_KEY in self._store_data:
                self._encryption_key = self._store_data.get(STORAGE_DATA_KEY)

            else:
                for store_data_key in self._store_data:
                    if store_data_key == self._entry_id:
                        entry_configuration = self._store_data[store_data_key]

                        if STORAGE_DATA_KEY in entry_configuration:
                            self._encryption_key = entry_configuration.get(
                                STORAGE_DATA_KEY
                            )

                            entry_configuration.pop(STORAGE_DATA_KEY)

        if self._encryption_key is None:
            self._encryption_key = Fernet.generate_key().decode("utf-8")

        self._crypto = Fernet(self._encryption_key.encode())

    async def remove(self):
        if self._entry_id in self._store_data:
            self._is_set_up_mode = True

            self._store_data.pop(self._entry_id)

            await self._save()

    async def _save(self):
        if self._store is None:
            return

        if self._store_data is None:
            self._store_data = {STORAGE_DATA_KEY: self._encryption_key}

        elif STORAGE_DATA_KEY not in self._store_data:
            self._store_data[STORAGE_DATA_KEY] = self._encryption_key

        if not self._is_set_up_mode:
            if self._entry_id not in self._store_data:
                self._store_data[self._entry_id] = {}

            for key in self._data:
                if key not in [CONF_PASSWORD, CONF_USERNAME]:
                    self._store_data[self._entry_id][key] = self._data[key]

            for key in [CONF_PASSWORD, CONF_USERNAME]:
                if key in self._store_data[self._entry_id]:
                    self._store_data[self._entry_id].pop(key)

        await self._store.async_save(self._store_data)

    def _encrypt(self, data: str) -> str:
        if data is not None:
            data = self._crypto.encrypt(data.encode()).decode()

        return data

    def _decrypt(self, data: str) -> str:
        if data is not None and len(data) > 0:
            data = self._crypto.decrypt(data.encode()).decode()

        return data
