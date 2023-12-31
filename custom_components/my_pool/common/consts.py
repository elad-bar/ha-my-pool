from datetime import timedelta

DOMAIN = "my_pool"
DEFAULT_NAME = "MyPool"
MANUFACTURER = "Magen Ecoenergy"

UPDATE_API = timedelta(minutes=5)

SIGNAL_DEVICE_NEW = f"signal_{DOMAIN}_device_new"
CONFIGURATION_FILE = f"{DOMAIN}.config.json"

PRODUCT_URL = "https://www.magen-ecoenergy.com/"

CONF_FCM_TOKEN = "fcmToken"

STORAGE_DATA_KEY = "key"
STORAGE_DATA_TOKEN_KEY = "token"

API_MAX_ATTEMPTS = 3

DATA_ITEM_DEVICES = "device"
DATA_ITEM_MEMBER_DETAILS = "member-details"
DATA_ITEM_CONFIG = "configuration"

PRODUCT_PAGE = {"G+": "resilience_g"}

ATTR_ATTRIBUTES = "attributes"
ATTR_ACTIONS = "actions"
ATTR_IS_ON = "is_on"

ACTION_ENTITY_TURN_ON = "turn_on"
ACTION_ENTITY_TURN_OFF = "turn_off"
ACTION_ENTITY_TOGGLE = "toggle"
ACTION_ENTITY_SELECT_OPTION = "select_option"
ACTION_ENTITY_SET_NATIVE_VALUE = "set_native_value"

CONFIG_USER_POWER = "config-user-power"
CONFIG_USER_COVER_POWER = "config-user-coverPower"
CONFIG_USER_PH = "config-user-ph"
CONFIG_USER_ORP = "config-user-orp"
CONFIG_USER_CL = "config-user-cl"
CONFIG_TECHNICIAN_POOL_SIZE = "config-technician-poolSize"
CONFIG_TECHNICIAN_ACID_PUMP_ENABLE = "config-technician-acidPump-enable"
IS_DEVICE_CONNECTED = "isDeviceConnected"
RUNTIME_DEVICE_ON = "runtime-device-on"
RUNTIME_DEVICE_TURBO = "runtime-device-turbo"
RUNTIME_DEVICE_TURBO_TIME = "runtime-device-turboTime"
RUNTIME_PH_VALUE = "runtime-ph-value"
RUNTIME_ORP_VALUE = "runtime-orp-value"
RUNTIME_SALINITY_VALUE = "runtime-salinity-value"
RUNTIME_CPU_TEMPERATURE_VALUE = "runtime-cpuTemperature-value"
RUNTIME_BOARD_TEMPERATURE_VALUE = "runtime-boardTemperature-value"
RUNTIME_WATER_TEMPERATURE_VALUE = "runtime-waterTemperature-value"
RUNTIME_CELL_TEMPERATURE_VALUE = "runtime-cell-temperature-value"
RUNTIME_ACID_PUMP_DAYS_LEFT = "runtime-acidPump-daysLeft"
NETWORK_SSID = "network-ssid"
NETWORK_RCPI = "network-rcpi"
CONFIG_AUTOMATION_CHANNEL_MODE = "config-automation-channel*-mode"
CONFIG_AUTOMATION_CHANNEL_STATE = "config-automation-channel*-state"
RUNTIME_AUTOMATION_STATE_CHANNEL_STATE = "runtime-automationState-channel*-state"
RUNTIME_AUTOMATION_STATE_CHANNEL_TIMELEFT = "runtime-automationState-channel*-timeLeft"
SALINITY_STATUS = "salinity-status"
SALT_MISSING = "salt-missing"
RUNTIME_POWER = "runtime-power"
RUNTIME_COVER_STATE = "runtime-coverState"
RUNTIME_AUTOMATION_PRESENT = "runtime-automationPresent"

UNIT_PH = "ph"

UPDATE_TELEMETRY_PARAMS = [
    CONFIG_USER_POWER,
    CONFIG_USER_COVER_POWER,
    CONFIG_USER_PH,
    CONFIG_USER_ORP,
    CONFIG_USER_CL,
    CONFIG_TECHNICIAN_POOL_SIZE,
]

MAXIMUM_SALINITY_PPM = 4500
MINIMUM_SALINITY_PPM = 3000
PREFERRED_SALINITY_PPM = 4000
NORMAL_SALINITY_PPM_RANGE = [3600, 4200]

BASE_SALINITY_PPM = 1000
SALT_WEIGHT_PER_SQM = 1
SALT_WEIGHT_FOR_PREFERRED_SALINITY = PREFERRED_SALINITY_PPM / BASE_SALINITY_PPM

TO_REDACT = [
    "id",
    "email",
    "phoneNumber",
    "hash",
    "fcmToken",
    "token",
    "serialNumber",
    "owner",
]
