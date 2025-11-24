@defgroup GetStarted
@addtogroup GetStarted
@{

# Get Started {#GetStarted}

## How to set up SonicControl

### Clone the repository

Navigate to the folder where you want the repository to be with `cd path/to/directory`.  
Clone the repository with `git clone git@github.com:usepat/soniccontrol.git`.  
Then open the repository in vscode.

### Install python

Install the right python version locally, so that you can run SonicControl. The current supported python versions are listed on the [Github Page](https://github.com/usepat/soniccontrol) or in the *pyproject.toml* file in the root directory of SonicControl. 

### Virtual environment

Open the root folder of SonicControl with your terminal of choice and initialize a python virtual environment.  
Note that the environment will have the same python version as the python interpreter you created it with. So choose a python interpreter with a version >= 3.10. 

> Note: python 3.12 has issues with ttkbootstrap, but 3.11 works fine

```
python3.10 -m venv .venv
```

#### Activating the virtual environment

To actually tell python to run a virtual environment one should run the following command.

##### Windows
```
.\.venv\Scripts\activate
```

##### MacOS & Linux
```
source ./.venv/bin/activate
```
or
```
. ./.venv/bin/activate
```

After running the corresponding command, the user should see the terminal reacting somehow and telling that the virtual environment is activated.

In vscode you can also create a .env file with 
```
PYTHONPATH=./.venv/bin/python
```
This will set the path correctly to the interpreter of the virtual environment.

For deactivating the venv use `deactivate`

### Installing Soniccontrol

In the created and activated virutal environment, the following command should be executed next.

```
pip install -e .
```

``pip`` is the Python Package installer, whereas ``-e`` tells ``pip``, that the installed code should be editable. This results into python declaring the root sourcecode as the actual application. The user can edit the sourcecode and run python without reinstalling the application.

#### Installing development libraries

To install development libraries, one should run the following command.
```
pip install -r requirements.txt
```

You can create a `requirements.txt` with `pip freeze > requirements.txt`. Do this each time you install new dependencies with `pip`.

## Running Soniccontrol

To run soniccontrol GUI, either run `soniccontrol_gui` as a command in the cli or execute *src/soniccontrol_gui/__main__.py*.

For the cli version of soniccontrol run `soniccontrol' as a command in the cli.

### Running SonicControl with a simulation

You can create a simulation executable of the firmware and provide the path to it over the `SIMULATION_EXE_PATH` environment variable. If you then start Sonic Control, a **Connect to simulation** button will appear in the connection window.  

## How to set up the documentation

### Install PlantUML and Doxygen

For the documentation Doxygen and PlantUML are needed, install both with:
```
sudo apt install doxygen default-jre plantuml
```
After that you have to set the environment variable `PLANTUML_JAR_PATH`. I recommend to just use a `.env` file for that or set it inside `~/.bashrc`.
```
PLANTUML_JAR_PATH="/usr/share/plantuml/plantuml.jar"
```

### Generate the documentation

To generate the documentation you can open the *Command Palette* in vscode with `Ctrl+P` and then execute `task Build Documentation`.
Alternatively you can also execute `doxygen ./docs/DoxyFile`.

The generated documentation will be put into the folder *./docs/output*.
You can open the file *./docs/output/html/index.html* in the browser to view the documentation.

On the page [Project Setup](@ref ProjectSetup) you will find information on how continuous integration and deployment is set up, how the program is packaged and how the whole pipeline for building works in the background and how it is configured.

@}