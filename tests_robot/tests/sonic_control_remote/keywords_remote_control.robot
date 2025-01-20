*** Settings ***

Resource    ../variables.robot

Library    sonic_robot.RobotRemoteController    log_path=${OUTPUT_DIR}    AS    RemoteController
Library    sonic_robot.conversion_utils

Variables    sonic_robot.field_names

*** Keywords ***

Connect to device
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
    [Arguments]    ${command_request}
    ${answer}=    RemoteController.Send Command     ${command_request}
    ${answer_message}=    Set Variable    ${answer}[0]
    ${is_answer_valid}=    Set Variable    ${answer}[2]

    Log    Answer received: "${answer_message}"
    Log    Is Answer Valid: "${is_answer_valid}"

    ${is_connected}=    RemoteController.Is connected to device
    Should Be True    ${is_connected}


Send command and check response
    [Arguments]    ${command_request}    ${should_be_valid}=${True}    &{expected_answer_values}
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