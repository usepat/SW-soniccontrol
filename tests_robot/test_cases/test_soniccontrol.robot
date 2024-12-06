*** Settings ***
Library    sonic_robot.RobotRemoteController    log_path=${OUTPUT_DIR}    AS    RemoteController
Variables    sonic_robot.variables

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect

Test Setup    Reconnect if disconnected
Test Teardown    RemoteController.Send Command     !OFF


*** Variables ***
${TARGET}             simulation        # can be either "simulation" or "url"
${SIMULATION_EXE_PATH}  ${None}
${URL}  ${None}




*** Test Cases ***

Set frequency updates device state
    ${frequency_answer}=    RemoteController.Set "frequency" to "10000"
    Should Contain    ${frequency_answer}[0]    10000 Hz
    Should Be True    ${frequency_answer}[1]

Send Example Commands
    ${command_examples_list}=    RemoteController.Deduce list of command examples
    FOR  ${command_example}  IN  @{command_examples_list}
        Run Keyword and Continue on Failure    Send Command    ${command_example} 
        Reconnect if disconnected
    END

*** Keywords ***

Connect to device
    IF    "${TARGET}" == 'simulation'
        IF    $SIMULATION_EXE_PATH is None
            Set Suite Variable    ${SIMULATION_EXE_PATH}    %{SIMULATION_EXE_PATH}    # robotcode: ignore
        END
        RemoteController.Connect via process to    ${SIMULATION_EXE_PATH}
    ELSE
        IF    "${URL}" == 'url'
            Fail    msg=No url to the serial port was provided
        END
        RemoteController.Connect via serial to    ${URL}
    END

Reconnect if disconnected
    ${connection_is_open}=    RemoteController.Is connected to device
    IF  not $connection_is_open
        RemoteController.Disconnect
        Connect to device
    END
    
    
Send Command
    [Arguments]    ${command_request}
    ${answer}=    RemoteController.Send Command     ${command_request}
    Log    Answer received: "${answer}[0]"
    Should Be True    ${answer}[1]        # check if answer is valid

