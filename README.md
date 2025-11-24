# SonicControl

## What is SonicControl?

SonicControl was developed by [usePAT](https://www.usepat.com/) as a control software to interact with their ultrasonic cleaning devices (SonicDescale, SonicClean, ...).
With it you can:
- Communicate directly with the devices via a serial monitor
- Record measurements
- Execute predefined procedures
- Execute custom scripts
- Create settings and configurations for the devices
- Flash firmware on to the devices

usePAT decided to make SonicControl open source, so that users can adapt the software to their use cases.

## Quick Project Overview

The project contains multiple folders and files with each having a specific responsibility:
- *src*: In this folder is all the application code
- *docs*: In this folder lays the documentation pages
- *scripts*: Helper scripts for building, packaging, etc.
- *tests*: unit tests with pytest
- *robot_tests*: system tests with robot framework
- *.vscode*: settings, tasks, etc. for vscode
- *.github*: Workflows for github actions, settings and other stuff related to github
- *pyproject.toml*: Contains meta data and settings for the python project
- *requirements.txt*: Contains the dependencies of this project 

The project is divided into single python packages in the *src* folder:
- *soniccontrol*: Is the core package, that contains the logic for the communication with the device, executing scripts and flashing.
- *soniccontrol_gui*: This package contains the main application. It is a user friendly GUI.
- *soniccontrol_cli* **Work in progress**: This is a cli version of soniccontrol.
- *sonicprotocol* **Work in progress**: This package contains preprocessor scripts to generate html, c++ and python code for the custom protocol used by the software and the devices to communicate with each other.
- *sonic_robot*: This package is a library for the robot framework. It is used for system testing.

Please read the rest of the documentation for a better understanding on how everything works and fits together.

## Installation Instructions for SonicControl(with pip)

### Prerequisites

First, ensure you have **Python 3.10** or newer installed.

#### On Windows:

- You can download the latest Python installer from [python.org](https://www.python.org/downloads/).
- If you don't want to override your current Python installation, make sure to **uncheck "Add to PATH"** during installation. After installation, you can create and manage virtual environments using `py`.

#### On Linux:

- You can install Python 3.10 using the apt package manager:

  ```bash
  sudo apt install python3.10
To manage multiple Python versions, you can use [Linux alternatives](https://man7.org/linux/man-pages/man1/update-alternatives.1.html) or [pyenv](https://github.com/pyenv/pyenv) to switch between versions.

### Setting Up a Virtual Environment (Recommended)

SonicControl has many dependencies, and it's recommended to create a virtual environment to avoid conflicts with existing Python packages. Some common packages that could cause conflicts include:
- async-tkinter-loop (for handling async in GUI applications)
- ttkbootstrap (for UI styling)
- attrs (for data validation)
- asyncio (for asynchronous programming)
- numpy (for numerical computations)

### On Windows & Linux:

You can create the virtual environment either by using `python` or specifying a specific version with `py` (on Windows) or `python3.10` (on Linux).

1. **Using `python`:** If `python` points to a version 3.10 or newer(run `python --version` to check this), you can simply use:

    ```bash
    python -m venv venv
    ```

2. **On Windows (using `py`):** If you have multiple versions of Python installed on Windows, you can specify the version using `py`:

    ```bash
    py -3.10 -m venv venv
    ```

3. **On Linux (using `python3.10`):** If you're on Linux and want to specify Python 3.10, use:

    ```bash
    python3.10 -m venv venv
    ```

Once you create the virtual environment, you can activate it and use `python` within the virtual environment. This will automatically use the Python version you specified when creating the environment.

### Activating the Virtual Environment:

- **On Windows:**

    ```bash
    .\venv\Scripts\activate
    ```

- **On Linux:**

    ```bash
    source venv/bin/activate
    ```

Once activated, the command `python` will use the version that you used to create the virtual environment.

### Deactivating the Virtual Environment:

When you're done working in the virtual environment, you can deactivate it by simply running:

```bash
deactivate
```

### Installing SonicControl

Once the virtual environment is activated, you can install the SonicControl package with one of the following methods:

#### Option 1: Install a Specific Release Tag
To install a specific release (e.g., `v2.3.0-beta`), use the following command:

```bash
pip install git+https://github.com/usepat/SW-soniccontrol@v2.3.0-beta
```
Replace v2.3.0-beta with the tag of the release you want to install.
Here you can find a list of all the [Releases](https://github.com/usepat/SW-soniccontrol/releases)

#### Option 2: Install the Latest Release on Windows

To always install the latest release, use the following three commands inside the virtual environment:

```batch
for /f "tokens=2 delims=:" %i in ('curl -s https://api.github.com/repos/usepat/SW-soniccontrol/releases/latest ^| findstr /i "tag_name"') do @set TAG=%i
set TAG=%TAG:~2,-1%
pip install git+https://github.com/usepat/SW-soniccontrol@%TAG%
````

#### Option 3: Install the Latest Release on Linux/macOS (Using `jq`)

To install the latest release on **Linux** or **macOS**, use the following one-liner:

```bash
pip install git+https://github.com/usepat/SW-soniccontrol@$(curl -s https://api.github.com/repos/usepat/SW-soniccontrol/releases/latest | jq -r .tag_name)
```

### Running the Application
To start the GUI, simply run the following command in the `activated` virtual environment:

```bash
soniccontrol
```
Alternatively, you can import `soniccontrol` in any Python program:
```bash
import soniccontrol
```
Altough this still needs to be tested and a guide for using soniccontrol in Python programs will be added later

## Get Started for Developers

For the setup please look at [Get Started](@ref GetStarted).
Or give you the full experience with [Project Setup](@ref ProjectSetup).  

> Btw, those links will only work after building the documentation. 
> If you have not builded the documentation yet use this [link](./docs/get_started.md) instead.


