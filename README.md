# Wifi Power measurement tests

This repository contains power measurement tests for the WiFI samples in [Nordic Connect SDK](www.github.com/nrfconnect/sdk-nrf) using the [PPK2](https://www.nordicsemi.com/Products/Development-hardware/Power-Profiler-Kit-2).

The [PPK2 API](https://github.com/IRNAS/ppk2-api-python) is used for interfacing with the PPK2.

The power measurement tests run on self-hosted runners. The firmware under test run on the nRF7002 DK.

### Oncommit
[![Build](https://github.com/balaji-nordic/wifi-power-meas-test/actions/workflows/build.yml/badge.svg?branch=main&event=push)](https://github.com/balaji-nordic/wifi-power-meas-test/actions/workflows/build.yml)
[![Test](https://github.com/balaji-nordic/wifi-power-meas-test/actions/workflows/test.yml/badge.svg?branch=main&event=push)](https://github.com/balaji-nordic/wifi-power-meas-test/actions/workflows/test.yml)

### Nightly
[![Nightly Test](https://github.com/balaji-nordic/wifi-power-meas-test/actions/workflows/test.yml/badge.svg?event=schedule)](https://github.com/balaji-nordic/wifi-power-meas-test/actions/workflows/test.yml)
