from dataclasses import dataclass

from custom_components.my_pool.common.consts import (
    CONFIG_AUTOMATION_CHANNEL_MODE,
    CONFIG_AUTOMATION_CHANNEL_STATE,
    CONFIG_TECHNICIAN_ACID_PUMP_ENABLE,
    CONFIG_TECHNICIAN_POOL_SIZE,
    CONFIG_USER_CL,
    CONFIG_USER_COVER_POWER,
    CONFIG_USER_ORP,
    CONFIG_USER_PH,
    CONFIG_USER_POWER,
    IS_DEVICE_CONNECTED,
    NETWORK_RCPI,
    NETWORK_SSID,
    RUNTIME_ACID_PUMP_DAYS_LEFT,
    RUNTIME_AUTOMATION_STATE_CHANNEL_STATE,
    RUNTIME_AUTOMATION_STATE_CHANNEL_TIMELEFT,
    RUNTIME_BOARD_TEMPERATURE_VALUE,
    RUNTIME_CELL_TEMPERATURE_VALUE,
    RUNTIME_CPU_TEMPERATURE_VALUE,
    RUNTIME_DEVICE_ON,
    RUNTIME_DEVICE_TURBO,
    RUNTIME_DEVICE_TURBO_TIME,
    RUNTIME_ORP_VALUE,
    RUNTIME_PH_VALUE,
    RUNTIME_SALINITY_VALUE,
    RUNTIME_WATER_TEMPERATURE_VALUE,
    UNIT_PH,
)
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)
from homeassistant.components.number import NumberDeviceClass, NumberEntityDescription
from homeassistant.components.select import SelectEntityDescription
from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.components.switch import SwitchEntityDescription
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS,
    EntityCategory,
    Platform,
    UnitOfElectricPotential,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
)
from homeassistant.helpers.entity import EntityDescription


@dataclass(slots=True)
class IntegrationEntityDescription(EntityDescription):
    platform: Platform | None = None


@dataclass(slots=True)
class IntegrationBinarySensorEntityDescription(
    BinarySensorEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.BINARY_SENSOR
    on_value: str | bool | None = None
    attributes: list[str] | None = None


@dataclass(slots=True)
class IntegrationSensorEntityDescription(
    SensorEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.SENSOR


@dataclass(slots=True)
class IntegrationSelectEntityDescription(
    SelectEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.SELECT


@dataclass(slots=True)
class IntegrationNumberEntityDescription(
    NumberEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.NUMBER


@dataclass(slots=True)
class IntegrationSwitchEntityDescription(
    SwitchEntityDescription, IntegrationEntityDescription
):
    platform: Platform | None = Platform.SWITCH
    on_value: str | bool | None = None


DEFAULT_ENTITY_DESCRIPTIONS: list[IntegrationEntityDescription] = [
    IntegrationNumberEntityDescription(
        key=CONFIG_USER_POWER,
        name="Power on Cover Closed",
        device_class=NumberDeviceClass.POWER_FACTOR,
        entity_category=EntityCategory.CONFIG,
        native_min_value=0,
        native_max_value=100,
        icon="mdi:lock",
    ),
    IntegrationNumberEntityDescription(
        key=CONFIG_USER_COVER_POWER,
        name="Power on Cover Opened",
        device_class=NumberDeviceClass.POWER_FACTOR,
        entity_category=EntityCategory.CONFIG,
        native_min_value=0,
        native_max_value=100,
        icon="mdi:lock-open",
    ),
    IntegrationNumberEntityDescription(
        key=CONFIG_USER_PH,
        name="PH",
        native_min_value=6.5,
        native_max_value=8.5,
        native_step=0.1,
        native_unit_of_measurement=UNIT_PH,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:ph",
    ),
    IntegrationNumberEntityDescription(
        key=CONFIG_USER_ORP,
        name="ORP",
        device_class=NumberDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        native_min_value=550,
        native_max_value=800,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
    ),
    IntegrationSensorEntityDescription(
        key=CONFIG_USER_CL,
        name="Chlorine Level",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
    ),
    IntegrationNumberEntityDescription(
        key=CONFIG_TECHNICIAN_POOL_SIZE,
        name="Pool Size",
        device_class=NumberDeviceClass.WATER,
        native_unit_of_measurement=UnitOfVolume.CUBIC_METERS,
        native_min_value=1,
        native_max_value=100,
        native_step=1,
        entity_category=EntityCategory.CONFIG,
        icon="mdi:move-resize",
    ),
    IntegrationSwitchEntityDescription(
        key=CONFIG_TECHNICIAN_ACID_PUMP_ENABLE,
        name="Acid Pump Enabled",
        on_value="1",
        entity_category=EntityCategory.CONFIG,
    ),
    IntegrationBinarySensorEntityDescription(
        key=IS_DEVICE_CONNECTED,
        name="Connected",
        on_value=str(True).lower(),
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    IntegrationSwitchEntityDescription(
        key=RUNTIME_DEVICE_ON, name="Power", on_value="1"
    ),
    IntegrationBinarySensorEntityDescription(
        key=RUNTIME_DEVICE_TURBO,
        name="Turbo",
        on_value="1",
        icon="mdi:truck-fast-outline",
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_DEVICE_TURBO_TIME,
        name="Turbo Time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:truck-fast-outline",
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_PH_VALUE,
        name="PH",
        native_unit_of_measurement=UNIT_PH,
        icon="mdi:ph",
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_ORP_VALUE,
        name="ORP",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_SALINITY_VALUE,
        name="Salinity",
        icon="mdi:shaker-outline",
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_CPU_TEMPERATURE_VALUE,
        name="CPU Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_BOARD_TEMPERATURE_VALUE,
        name="Board Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_WATER_TEMPERATURE_VALUE,
        name="Water Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:pool-thermometer",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_CELL_TEMPERATURE_VALUE,
        name="Cell Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    IntegrationSensorEntityDescription(
        key=RUNTIME_ACID_PUMP_DAYS_LEFT,
        name="Acid Pump Days Left",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        icon="mdi:autorenew",
    ),
    IntegrationSensorEntityDescription(
        key=NETWORK_SSID, name="SSID", entity_category=EntityCategory.DIAGNOSTIC
    ),
    IntegrationSensorEntityDescription(
        key=NETWORK_RCPI,
        name="Signal",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
]

for i in range(1, 8):
    index = str(i)
    automation_components = [
        IntegrationSelectEntityDescription(
            key=CONFIG_AUTOMATION_CHANNEL_MODE.replace("*", index),
            name=f"Automation {i} Mode",
            entity_category=EntityCategory.CONFIG,
            options=["0"],
        ),
        IntegrationSwitchEntityDescription(
            key=CONFIG_AUTOMATION_CHANNEL_STATE.replace("*", index),
            name=f"Automation {i}",
            on_value="1",
            entity_category=EntityCategory.CONFIG,
        ),
        IntegrationSensorEntityDescription(
            key=RUNTIME_AUTOMATION_STATE_CHANNEL_TIMELEFT.replace("*", index),
            name=f"Automation {i} Time Left",
            device_class=SensorDeviceClass.DURATION,
            native_unit_of_measurement=UnitOfTime.MINUTES,
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
        IntegrationBinarySensorEntityDescription(
            key=RUNTIME_AUTOMATION_STATE_CHANNEL_STATE.replace("*", index),
            name=f"Automation {i}",
            on_value="1",
            entity_category=EntityCategory.DIAGNOSTIC,
        ),
    ]

    DEFAULT_ENTITY_DESCRIPTIONS.extend(automation_components)
