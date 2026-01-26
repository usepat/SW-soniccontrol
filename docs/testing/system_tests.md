@defgroup SystemTests
@ingroup Testing
@addtogroup SystemTests
@{

# System and Integration Testing {#SystemTests}

In contrast to [Unit testing](@ref UnitTests), System testing is about testing the whole system and not just a single unit of it.
There is also integration testing, that focus on testing if a collection of units works together as expected. The transition from integration testing to system testing is fluid.

For the integration testing we use a binary of our [firmware](https://github.com/usepat/FW-sonic-firmware/tree/stable) that simulates it locally on the pc (but only for Linux). 
We can start this binary as a process in the command line and can communicate with it over `stdout` and `stdin`.
In the code we do this over [CLIConnectionFactory](@ref soniccontrol.ConnectionFactory.CLIConnectionFactory).

For testing the GUI we use the GUIDriver class. Every widget gets registered over a name and the GUIDriver offers methods to interact with the widgets programmatically.

Because for the simulation and real device (and also for different device types like postman and worker) we need to interact differently with the GUI to open the device window. Therefore we use a Strategy pattern for Connecting with the Device and opening the Device Window.

For writing the system tests we used the robot framework but now we want to migrate to pytest.

## Robot Framework

The [Robot Framework](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html) is a popular testing framework for system tests. 
You can install robot framework via `pip install robot-framework`.
You can write Python libraries for it as API and then use them together with thousand others libraries, provided by the robot community.
The *src/sonic_robot* folder contains the robot library for testing the application code.d
In the *tests_robots/test_cases* folder are the tests.

Here is an example for a robot file
```robot
*** Settings ***
Library    calculator.py
Suite Setup    Log    Starting Calculator Tests
Suite Teardown    Log    Calculator Tests Finished

*** Variables ***
${A}    10
${B}    5
${ZERO}    0

*** Test Cases ***

Addition Test
    [Documentation]    Verify that the addition function returns the correct sum.
    ${result}=    Add    ${A}    ${B}
    Should Be Equal    ${result}    15

Division Test
    [Documentation]    Verify that the division function returns the correct quotient.
    ${result}=    Divide    ${A}    ${B}
    Should Be Equal    ${result}    2

Division By Zero Test
    [Documentation]    Verify that dividing by zero raises an exception.
    Run Keyword And Expect Error    ValueError    Divide    ${A}    ${ZERO}
```
The framework creates you reports in html and logs for your tests.
They can be found in *tests_robots/results*.
The path is specified via *.vscode/settings.json*:
```json
"robotcode.robot.outputDir": "${workspaceFolder}/tests_robot/results"
```

To run robot you can us the vscode *Test Tab* or run them directly via `robot .` in the command line.

For continuous integration with robot see this [page](@ref CIandCD)

### Custom Tags

You can add tags to your tests, to group them and filter those you want to run.

Here an example of how to add and remove tags.
```robot
*** Settings ***
Test Tags       requirement: 42    smoke


*** Test Cases ***

Own tags
    [Documentation]    Test has tags 'requirement: 42', 'smoke' and 'not ready'.
    [Tags]    not ready
    No Operation


Remove common tag
    [Documentation]    Test has only tag 'requirement: 42'.
    [Tags]    -smoke
    No Operation  
```

To select which tests to run, you can specify which tags:
```
robot tests.robot
--include fooANDbar     # Matches tests containing tags 'foo' and 'bar'.
--exclude xx&yy&zz      # Matches tests containing tags 'xx', 'yy', and 'zz'.
```

Those are the tags used in this project:
- worker: For the worker devices
- descaler: For the descale devices
- expensive_to_run: For tests that take a long time to complete

### Profiles

With the RobotCode extension, we can define profiles in a *robot.toml* file.  
A profile defines a set of arguments (which variables to set, which tags to include, etc...) that are passed to the commandline to start the robot tests.

We have a profile for each device type and the simulation. In the vscode testing tab you can select which profile to run the tests with.

@}