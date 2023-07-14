# Home Assistant integration to Magen Eco-energy My-Pool devices

Monitor ~~and control~~ your Resilience G/G+ devices using My-Pool (Magen Eco-energy) app from Home Assistant,
Integration also calculates how much additional salt to add when needed.

## How to

#### Requirements

Account for My-Pool

#### Installations via HACS [![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

- In HACS, look for "My-Pool" and install and restart
- If integration was not found, please add custom repository `elad-bar/ha-my-pool` as integration
- In Settings --> Devices & Services - (Lower Right) "Add Integration"

#### Setup

To add integration use Configuration -> Integrations -> Add `My Pool`
Integration supports **multiple** accounts and devices

| Fields name | Type    | Required | Default | Description         |
| ----------- | ------- | -------- | ------- | ------------------- |
| Username    | Textbox | +        | -       | Username of account |
| Password    | Textbox | +        | -       | Password of account |

###### Validation errors

| Errors                    |
| ------------------------- |
| Invalid credentials (403) |

## Run API over CLI

### Requirements

- Python 3.10
- Python virtual environment
- Install all dependencies, using `pip install -r requirements.txt` command

### Environment variables

| Environment Variable | Type    | Default | Description                                                                                                               |
| -------------------- | ------- | ------- | ------------------------------------------------------------------------------------------------------------------------- |
| USERNAME             | String  | -       | Username used for My-Pool                                                                                                 |
| PASSWORD             | String  | -       | Password used for My-Pool                                                                                                 |
| DEBUG                | Boolean | False   | Setting to True will present DEBUG log level message while testing the code, False will set the minimum log level to INFO |

### Execution

Run file located in `tests/api_testing.py`

## Troubleshooting

### Logs

Before opening an issue, please provide logs related to the issue,
For debug log level, please add the following to your config.yaml

```yaml
logger:
  default: warning
  logs:
    custom_components.my_pool: debug
```

Or use the HA capability in device page:
Settings -> Devices & Services -> My Pool -> 3 dots menu -> Enable debug logging
When done and would like to extract the log:
Settings -> Devices & Services -> My Pool -> 3 dots menu -> Disable debug logging

Please attach also diagnostic details of the integration, available in:
Settings -> Devices & Services -> My Pool -> 3 dots menu -> Download diagnostics
