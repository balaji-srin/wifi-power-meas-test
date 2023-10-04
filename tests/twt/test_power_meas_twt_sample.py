# Test to measure power consumption of wifi shell sample

from ppk2_api.ppk2_api import PPK2_MP as PPK2_API

import os
import time
import serial
import pytest
import logging
import matplotlib.pyplot as plt

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Get PPK Port and Device Port from environment variables
PPK_PORT = os.environ.get('PPK_PORT')   # Com port to interact with the PPK
DK_PORT = os.environ.get('DK_PORT')  # Com port to interact with the DK

ppk2 = None
ser = None

@pytest.fixture(scope="session")
def suite_setup():
    global ppk2
    global ser

    os.system("rm -rf test_results")

    if (PPK_PORT is None):
        raise (IOError("PPK_PORT is not set"))
    if (DK_PORT is None):
        raise (IOError("DK_PORT is not set"))

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

    build_cmd = f"west build {zephyr_base}/../nrf/samples/wifi/twt -b nrf7002dk_nrf5340_cpuapp"
    logger.debug(f"Building Sample: {build_cmd}")
    os.system(build_cmd)

    flash_cmd = "west flash"
    logger.debug(f"Flashing: {flash_cmd}")
    os.system(flash_cmd)

    reset_cmd = "nrfjprog --reset"
    logger.debug(f"Resetting {reset_cmd}")
    os.system(reset_cmd)

    ser = serial.Serial(DK_PORT, 115200, timeout=0.050)

    # Wait for the device to boot up
    time.sleep(2)

    yield

    logger.debug("Turning off Power")
    ppk2.toggle_DUT_power("OFF")

    os.system("mkdir test_results")
    os.system("mv current_samples*.png test_results")


# Function that measures the average current for a given time.
def avg_current_measure(time_in_seconds: int, file_name_suffix: str) -> int:
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

    # Remove any existing plots
    plt.clf()
    # Create a graph with current samples
    plt.plot(samples_cumulative)
    plt.ylabel('Current (uA)')
    plt.savefig(f'current_samples_{file_name_suffix}.png', dpi=300)

    return sum(samples_cumulative)/len(samples_cumulative)


def current_consumption_check(current_ua: int, expected_ua: int, threshold: float = 0.05) -> bool:
    delta_ua = expected_ua * threshold
    return ((expected_ua - delta_ua) <= current_ua <= (expected_ua + delta_ua))

def get_serial_output(time_in_seconds: int) -> int:
    LOOP_SLEEP_TIME_SECONDS = 0.1
    start_time = time.time()
    data_in = b''
    while (time.time() - start_time) < time_in_seconds:
        time.sleep(LOOP_SLEEP_TIME_SECONDS)
        while ser.in_waiting:
            data_in += ser.readline()
    return (data_in.decode())

def test_current_measurement(suite_setup):
    INITIAL_SLEEP_TIME_SECONDS = 2
    MEASUREMENT_TIME_SECONDS = 5
    time.sleep(INITIAL_SLEEP_TIME_SECONDS)
    current_ua = avg_current_measure(MEASUREMENT_TIME_SECONDS, file_name_suffix="twt")
    logger.debug(f"Average Current: {current_ua} uA")
    log_from_serial = get_serial_output(INITIAL_SLEEP_TIME_SECONDS + MEASUREMENT_TIME_SECONDS)
    logger.debug(f"Serial Output: {log_from_serial}")
    assert (current_consumption_check(current_ua, expected_ua=15, threshold=0.05))

