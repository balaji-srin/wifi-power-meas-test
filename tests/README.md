# WiFi Power Measurement Tests

This folder contains tests for measuring power consumption of a device using WiFi and shell commands.

## Description

The `test_power_meas_wifi_shell.py` script contains tests for measuring power consumption of a device using WiFi  shell commands.


## Prerequisites

Before running the tests in this script, ensure that the following prerequisites are met:

- The PPK2 is connected to the 7002 DK.
- The nRF7002 DK is pre-provisioned with the WIFI SSID and password. You can do that by flashing the shell sample and then using `wifi_cred add` command.
- Working python installation and all required python modules listed in `requirements.txt`.
- WOrking NCS toolchain required to build wifi shell.

## Usage

```
pytest .
```

## Results

The following images show the sample power consumption figures obtained by the test cases.

![Radio Off](sample_results/current_samples_radio_off.png)

![Scan state](sample_results/current_samples_scan_state.png)

![Connected state](sample_results/current_samples_connected_state.png)

![TWT State](sample_results/current_samples_twt_state.png)

![TWT Teardown state](sample_results/current_samples_twt_teardown_state.png)


