# Start with the Zephyr CI image
FROM ghcr.io/zephyrproject-rtos/ci:v0.26.2
WORKDIR /workdir

ARG NORDIC_COMMAND_LINE_TOOLS_VERSION="Versions-10-x-x/10-17-0/nrf-command-line-tools-10.17.0"

# Copy the requirements.txt file to the container
COPY tests/requirements.txt .

# Install the Python modules specified in requirements.txt
RUN pip install -r requirements.txt

# Remove the requirements.txt file
RUN rm requirements.txt

RUN echo "Installing dependencies for nRFCommand line tools" && \
    apt-get update && \
    apt-get install libxcb-render-util0-dev -y && \
    apt-get install libxrender1 libxcb-shape0 libxcb-randr0 libxcb-icccm4 libxcb-keysyms1 libxcb-image0 libxkbcommon-x11-0 -y

# Nordic command line tools
ARG NCLT_URL="https://www.nordicsemi.com/-/media/Software-and-other-downloads/Desktop-software/nRF-command-line-tools/sw/${NORDIC_COMMAND_LINE_TOOLS_VERSION}_Linux-amd64.tar.gz"
RUN echo "NCLT_URL=${NCLT_URL}" && \
    mkdir tmp && cd tmp && \
    wget -qO - "${NCLT_URL}" | tar --no-same-owner -xz && \
    # Install included JLink
    DEBIAN_FRONTEND=noninteractive apt-get -y install ./*.deb && \
    # Install nrf-command-line-tools
    cp -r ./nrf-command-line-tools /opt && \
    ln -s /opt/nrf-command-line-tools/bin/nrfjprog /usr/local/bin/nrfjprog && \
    ln -s /opt/nrf-command-line-tools/bin/mergehex /usr/local/bin/mergehex && \
    cd .. && rm -rf tmp
