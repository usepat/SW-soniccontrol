@defgroup Deployment
@ingroup ProjectSetup
@addtogroup Deployment
@{

# Deployment {#Deployment}

Python projects can be packaged so that they can be later uploaded to [PyPI](https://pypi.org/).
This is useful for distributing the python project as a library and exactly that is what we want with [SonicControl](@ref sonic_control).
Also the packaging is needed for distributing it via an installer.
Another use case for packaging is to install the software in editable mode via `pip install -e .`. 
This is needed for [unit testing](@ref UnitTests) and [system testing](@ref SystemTests).

## Packaging with Setuptools

[Setuptools](https://setuptools.pypa.io/en/latest/userguide/index.html) is a python backend for packaging a python project. 
In the *pyproject.toml* file we can specify the version, name, authors, etc. of the project and configure setuptools on how to build the package.
```toml
[build-system]
requires = ["setuptools>=42", "wheel", "setuptools-git-versioning>=2.0,<3"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
zip-safe = true
# Include package data is needed so that the resources get shipped with the package
include-package-data = true

[tool.setuptools.packages.find]
where = ["src"]

# We use this to automatically get the version from the git tags
[tool.setuptools-git-versioning]
enabled = true
```
In the *pyproject.toml* file we can also specify configurations for other tools used like linters and testing frameworks.

To include resources correctly in our python project, we cannot access them directly by specifying relative paths via `pathlib.Path` and them load them.  
Instead we need to use `importlib.resources` to construct the Path correctly. 
```python
from importlib import resources as rs

LOGGING_CONFIG = Path(str(rs.files(soniccontrol_gui).joinpath("log_config.json")))
```

## Installation for windows with Inno Installer

For creating an installer we first create an executable of our software with [pyinstaller](https://pyinstaller.org/en/stable/index.html).
This is done via the bash script *scripts/create_exe.bat* (on Windows) and *scripts/create_exe.sh* (on Linux).  
There exists also a vscode task `Build SonicControl with PyInstaller` for it.  
The installer takes or editable package of the software and creates an exe for it. 
It accepts various arguments on what files to include and if the exe should open a window or run in the background.

After that we need to create an installer.
For this we use [Inno Installer](https://jrsoftware.org/isinfo.php).
Inno Installer takes a configuration \*.iss-file as input where various stuff is defined as what icon to use, in which directory to install stuff, etc.
Note that Inno Installer does not work on linux, so this step has to be done on windows or on a virtual machine. 

For on how to use continuous deployment, check out this [page](@ref CIandCD)

## Installation on Linux via AppImage

AppImage is a format, where a single file contains the whole application with all dependencies. For that the bundled dir output from PyInstaller muss be placed inside an AppDir structure following the AppImage format. With the AppImageTool the final AppImage can then be created. This is all done in *scripts/linux_deployment/create_app_image.sh*. For the script to work, you do not have to install app image tool, as it resides inside the tool folder.

## Uploading to PyPI

Work in progress...  
This is not done yet and has to be implemented.

@}