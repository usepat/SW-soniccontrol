# Start with a base image
FROM ubuntu:20.04

WORKDIR /testing_environment

# Set environment variables to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Step 1: Install basic tools and software-properties-common for add-apt-repository
RUN apt-get update && \
    apt-get install -y software-properties-common

# Step 2: Add the toolchain PPA for newer GCC and G++
RUN add-apt-repository ppa:ubuntu-toolchain-r/test && \
    apt-get update

# Step 3: Install the rest of the packages, including g++-11 and gcc-11
RUN apt-get install -y \
    git \
    openssh-client \
    doxygen \
    graphviz \
    mscgen \
    dia \
    wget \
    build-essential \
    g++-11 \
    gcc-11 \
    libpthread-stubs0-dev \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libffi-dev \
    curl \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    liblzma-dev

# Download and compile Python 3.10 from source
RUN wget https://www.python.org/ftp/python/3.10.12/Python-3.10.12.tgz && \
    tar -xzf Python-3.10.12.tgz && \
    cd Python-3.10.12 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall && \
    cd .. && \
    rm -rf Python-3.10.12 Python-3.10.12.tgz

# Force creation of symbolic links for Python 3.10 and pip3.10
RUN ln -sf /usr/local/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/local/bin/pip3.10 /usr/bin/pip3

# Set GCC and G++ 11 as the default versions
RUN update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-11 100 && \
    update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-11 100

# Download and install CMake 3.22+
RUN wget https://github.com/Kitware/CMake/releases/download/v3.22.0/cmake-3.22.0-linux-x86_64.sh && \
    chmod +x cmake-3.22.0-linux-x86_64.sh && \
    ./cmake-3.22.0-linux-x86_64.sh --skip-license --prefix=/usr/local && \
    rm cmake-3.22.0-linux-x86_64.sh

# Set up SSH key and clone the repository
RUN mkdir -p /root/.ssh && chmod 700 /root/.ssh
COPY ssh_workflow /root/.ssh/id_ed25519
RUN chmod 600 /root/.ssh/id_ed25519
ENV GIT_SSH_COMMAND="ssh -i /root/.ssh/id_ed25519 -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no"
ARG SONICFIRMWARE_URL=git@github.com:usepat/FW-sonic-firmware.git
RUN git clone $SONICFIRMWARE_URL /testing_environment/FW-sonic-firmware

# Configure and build project
WORKDIR /testing_environment/FW-sonic-firmware
RUN git pull && git submodule update --init --recursive && git fetch --all --tags
RUN latest_tag=$(git describe --tags `git rev-list --tags --max-count=1`) && git checkout $latest_tag

# Set up Python virtual environment and install dependencies
WORKDIR /testing_environment
RUN python3 -m venv venv && /testing_environment/venv/bin/pip install robotframework

# Default command
CMD ["/bin/bash"]
