*** Settings ***
Library    sonic_robot.RobotRemoteController    log_path=${OUTPUT_DIR}    AS    RemoteController
Variables    sonic_robot.variables

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect



*** Variables ***
${TARGET}             simulation        # can be either "simulation" or "url"
${SIMULATION_EXE_PATH}  ${None}
${URL}  ${None}



*** Test Cases ***

Set frequency updates device state
    ${frequency}=    RemoteController.Set "frequency" to "1000000"
    Should Contain    ${frequency}    1000000 Hz



*** Keywords ***
Connect to device
    # Debugging: log the value of SIMULATION_EXE_PATH
    Log    SIMULATION_EXE_PATH: ${SIMULATION_EXE_PATH}

    IF  '${TARGET}' == 'simulation'
        # Check if SIMULATION_EXE_PATH is empty or None and set it accordingly
        IF    ${{$SIMULATION_EXE_PATH is None}}
            ${SIMULATION_EXE_PATH}= Get Environment Variable    SIMULATION_EXE_PATH    ${None}
        END
        

        # Log the final simulation path for debugging
        Log    Simulation path: ${SIMULATION_EXE_PATH}

        # Connect via process to SIMULATION_EXE_PATH
        RemoteController.Connect via process to    ${SIMULATION_EXE_PATH}
    ELSE
        # Check for URL
        IF  ${URL} == ${None}
            Fail    No URL to the serial port was provided
        END
        RemoteController.Connect via serial to    ${URL}
    END




       