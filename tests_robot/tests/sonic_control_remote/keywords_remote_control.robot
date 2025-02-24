*** Settings ***

Resource    ../variables.robot

Library    sonic_robot.RobotRemoteController    log_path=${OUTPUT_DIR}    AS    RemoteController
Library    sonic_robot.conversion_utils

Variables    sonic_robot.field_names

*** Keywords ***

Connect to device
    [Documentation]    Tries to connect over simulation or url to the device, depending, on what target is set
    IF    "${TARGET}" == 'simulation'
        IF    $SIMULATION_EXE_PATH is None
            Set Suite Variable    ${SIMULATION_EXE_PATH}    %{SIMULATION_EXE_PATH}    # robotcode: ignore
        END
        RemoteController.Connect via process to    ${SIMULATION_EXE_PATH}
    ELSE
        IF    $URL is None
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
    
Reconnect
    RemoteController.Disconnect
    Connect to device

    
Send command and check if the device crashes
    [Documentation]    Sends a command and then checks if the remote controller is still connected to the device
    [Arguments]    ${command_request}
    [Timeout]    1 minute 00 seconds
    ${answer}=    RemoteController.Send Command     ${command_request}
    
    ${answer_message}=    Set Variable    ${answer}[0]
    ${is_answer_valid}=    Set Variable    ${answer}[2]

    Log    Answer received: "${answer_message}"
    Log    Is Answer Valid: "${is_answer_valid}"

    ${is_connected}=    RemoteController.Is connected to device
    Should Be True    ${is_connected}


Send command and check response
    [Documentation]    Sends a command and checks if it is valid. 
    ...    Then it checks if the field values of the answer are equal to the expected values given in the arguments.
    [Arguments]    ${command_request}    ${should_be_valid}=${True}    &{expected_answer_values}
    [Timeout]    0 minute 30 seconds
    ${answer}=    RemoteController.Send Command     ${command_request}
    ${answer_message}=    Set Variable    ${answer}[0]
    ${answer_value_dict}=    Set Variable    ${answer}[1]
    ${is_answer_valid}=    Set Variable    ${answer}[2]

    Log    Sended command: "${command_request}"
    Log    Answer received: "${answer_message}"

    Should Be Equal    ${is_answer_valid}    ${should_be_valid}
    FOR  ${field_name}    ${expected_value}  IN  &{expected_answer_values}
        Should Be Equal    ${answer_value_dict}[${field_name}]    ${expected_value}
    END