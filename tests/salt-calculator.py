import json

from custom_components.my_pool.common.consts import (
    MAXIMUM_SALINITY_PPM,
    MINIMUM_SALINITY_PPM,
    NORMAL_SALINITY_PPM_RANGE,
    PREFERRED_SALINITY_PPM,
    SALT_WEIGHT_FOR_PREFERRED_SALINITY,
    UPDATE_TELEMETRY_PARAMS,
)

POOL_SIZE_SQM = 33
CURRENT_SALINITY_PPM = 3600


def get_missing_salt(pool_size, current_salinity) -> float:
    required_salt = pool_size * SALT_WEIGHT_FOR_PREFERRED_SALINITY
    salinity_gap = 1 - (current_salinity / PREFERRED_SALINITY_PPM)
    missing_salt = salinity_gap * required_salt

    return missing_salt


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


def test_salinity_status():
    print("Salinity status tests")
    test_params = [0, 1000, 2000, 3000, 3500, 3600, 4000, 4100, 4200, 4300, 4500, 5000]

    for test_param in test_params:
        status = _get_salinity_status(test_param)

        print(f"{test_param}: {status}")


# test_salinity_status()
value = 37.0

for key in UPDATE_TELEMETRY_PARAMS:
    key_parts = key.split("-")

    request_data = {
        "_deviceId": 132,
        "data": {},
    }

    data_item = request_data["data"]

    for key_part in key_parts:
        data_item[key_part] = int(value) if key_part == key_parts[len(key_parts) - 1] else {}

        data_item = data_item[key_part]

    print(json.dumps(request_data, indent=4))
