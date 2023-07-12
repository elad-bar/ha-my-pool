import asyncio
import json
import logging
import os
import sys

from custom_components.my_pool.managers.rest_api import RestAPI
from custom_components.my_pool.managers.config_manager import (
    ConfigManager,
)
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME

DEBUG = str(os.environ.get("DEBUG", False)).lower() == str(True).lower()
USERNAME = os.environ.get("USERNAME", False)
PASSWORD = os.environ.get("PASSWORD", False)

log_level = logging.DEBUG if DEBUG else logging.INFO

root = logging.getLogger()
root.setLevel(log_level)

stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(log_level)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
stream_handler.setFormatter(formatter)
root.addHandler(stream_handler)

_LOGGER = logging.getLogger(__name__)


class Test:
    def __init__(self):
        config_manager = ConfigManager(None, None)

        data = {
            CONF_USERNAME: USERNAME,
            CONF_PASSWORD: PASSWORD,
        }

        config_manager.update_credentials(data)

        self._config_manager = config_manager
        self._api = RestAPI(None, config_manager)

    async def list_data(self):
        await self._config_manager.initialize()

        await self._api.initialize()
        await self._api.update()

        for device_id in self._api.devices:
            device_id = self._api.get_device_data(device_id)

            _LOGGER.info(f"{device_id}: {json.dumps(device_id, indent=4)}")

        await self._api.terminate()

    async def terminate(self):
        await self._api.terminate()


loop = asyncio.new_event_loop()

instance = Test()

try:
    loop.create_task(instance.list_data())
    loop.run_forever()


except KeyboardInterrupt:
    _LOGGER.info("Aborted")

except Exception as rex:
    _LOGGER.error(f"Error: {rex}")
