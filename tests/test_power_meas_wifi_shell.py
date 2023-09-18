# Test to measure power consumption of wifi shell sample

from ppk2_api.ppk2_api import PPK2_MP as PPK2_API

import os
import time
import serial
import pytest
import logging

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

PPK_PORT = "/dev/ttyACM2"
DEVICE_PORT = "/dev/ttyACM1"

SCAN_STATE_DURATION_SECONDS = 3
CONNECTED_STATE_MEAS_DURATION_SECONDS = 2

ppk2 = None
ser = None


@pytest.fixture(scope="session")
def suite_setup():
    global ppk2
    global ser
    ppks_connected = PPK2_API.list_devices()
    if (len(ppks_connected) == 1):
        ppk_port = ppks_connected[0]
        logger.debug(f'Found PPK2 at {ppk_port}')
    else:
        raise (IOError(f'Too many or No connected PPK2\'s: {ppks_connected}'))

    ppk2 = PPK2_API(PPK_PORT)  # serial port will be different for you

    ppk2.get_modifiers()
    ppk2.use_source_meter()  # set source meter mode
    ppk2.set_source_voltage(3300)  # set source voltage in mV

    logger.debug("Turning on Power")
    ppk2.toggle_DUT_power("ON")

    zephyr_base = os.environ.get('ZEPHYR_BASE')

    build_cmd = f"west build {zephyr_base}/../nrf/samples/wifi/shell -b nrf7002dk_nrf5340_cpuapp"
    logger.debug(f"Building Wifi Shell Sample: {build_cmd}")
    os.system(build_cmd)

    flash_cmd = "west flash"
    logger.debug(f"Flashing Wifi Shell Sample: {flash_cmd}")
    os.system(flash_cmd)

    reset_cmd = "nrfjprog --reset"
    logger.debug(f"Resetting {reset_cmd}")
    os.system(reset_cmd)

    ser = serial.Serial(DEVICE_PORT, 115200, timeout=0.050)

    yield

    logger.debug("Turning off Power")
    ppk2.toggle_DUT_power("OFF")


def avg_current_measure(time_in_seconds: int) -> int:
    LOOP_SLEEP_TIME_SECONDS = 0.01
    samples_cumulative = []
    start_time = time.time()
    ppk2.start_measuring()
    while (time.time() - start_time) < time_in_seconds:
        read_data = ppk2.get_data()
        if read_data != b'':
            samples, _ = ppk2.get_samples(read_data)
            samples_cumulative += samples
        time.sleep(LOOP_SLEEP_TIME_SECONDS)
    ppk2.stop_measuring()
    if len(samples_cumulative) == 0:
        raise ValueError("No samples collected")

    return sum(samples_cumulative)/len(samples_cumulative)


def get_serial_output(time_in_seconds: int) -> int:
    LOOP_SLEEP_TIME_SECONDS = 0.1
    start_time = time.time()
    data_in = b''
    while (time.time() - start_time) < time_in_seconds:
        time.sleep(LOOP_SLEEP_TIME_SECONDS)
        while ser.in_waiting:
            data_in += ser.readline()
    return (data_in.decode())


def shell_command(cmd: str, cmd_output_wait_time_seconds: int = 1):
    ser.write(cmd.encode())
    return get_serial_output(cmd_output_wait_time_seconds)


def current_consumption_check(current_ua: int, expected_ua: int, threshold: float = 0.05) -> bool:
    delta_ua = expected_ua * threshold
    return ((expected_ua - delta_ua) <= current_ua <= (expected_ua + delta_ua))


def test_radio_off_current(suite_setup):
    current_ua = avg_current_measure(1)
    print(f"Average Current when radio is off: {current_ua} uA")
    assert (current_consumption_check(current_ua, expected_ua=5502, threshold=0.10))


def test_scan_current(suite_setup):
    shell_command("wifi scan\r\n")
    time.sleep(0.1)
    current_ua = avg_current_measure(SCAN_STATE_DURATION_SECONDS)
    logger.debug(f"Average Scan Current: {current_ua} uA")
    assert (current_consumption_check(current_ua, expected_ua=58442))


def test_connected_state_current(suite_setup):
    logger.debug("Connecting to prestored Wifi SSID: ")
    output = shell_command(f"wifi_cred auto_connect\r\n", 10)

    if "CTRL-EVENT-CONNECTED" not in output:
        logger.error("Failed to connect to Wifi")
        assert (False)

    meas_duration_seconds = CONNECTED_STATE_MEAS_DURATION_SECONDS
    current_ua = avg_current_measure(meas_duration_seconds)
    logger.debug(
        f"Average connected Current: {current_ua} uA for {meas_duration_seconds} seconds")

    #TODO: Reduce the threshold
    assert (current_consumption_check(current_ua, expected_ua=10000, threshold=0.50))


@pytest.mark.dependency(depends=["test_connected_state_current"])
def test_twt_current(suite_setup):
    TWT_WAKE_DURATION_US = 8192
    TWT_WAKE_INTERVAL_US = 2007000
    NO_OF_TWT_INTERVALS_TO_MEASURE = 3
    output = shell_command(
        f"wifi twt quick_setup {TWT_WAKE_DURATION_US} {TWT_WAKE_INTERVAL_US}\r\n", 3)
    if ("TWT accept" not in output):
        logger.error("Failed to get TWT from AP")
        assert (False)

    meas_duration_seconds = TWT_WAKE_INTERVAL_US * \
        NO_OF_TWT_INTERVALS_TO_MEASURE / 1000000
    current_ua = avg_current_measure(meas_duration_seconds)

    logger.debug(
        f"Average TWT state Current: {current_ua} uA for {meas_duration_seconds} seconds")

    assert (current_consumption_check(current_ua, expected_ua=424))


@pytest.mark.dependency(depends=["test_twt_current"])
def test_post_twt_teardown_current(suite_setup):
    measurement_duration_seconds = 2
    output = shell_command("wifi twt teardown_all\r\n")
    time.sleep(1)
    avg_twt_current = avg_current_measure(measurement_duration_seconds)
    if ("success" not in output):
        logger.error("Failed to tear down TWT")
        assert (False)
    logger.debug(
        f"Average Current after TWT tear down: {avg_twt_current} uA for {measurement_duration_seconds} seconds")
    assert (current_consumption_check(avg_twt_current, expected_ua=3770, threshold=0.10))
