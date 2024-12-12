*** Settings ***
Library    sonic_robot.RobotRemoteController    log_path=${OUTPUT_DIR}    AS    RemoteController
Variables    sonic_robot.variables
Variables    sonic_robot.field_names

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect

Test Setup    Reconnect if disconnected
Test Teardown    RemoteController.Send Command     !OFF


*** Variables ***
${TARGET}             simulation        # can be either "simulation" or "url"
${SIMULATION_EXE_PATH}  ${None}
${URL}  ${None}

${MIN_FREQUENCY}    ${100000}
${MAX_FREQUENCY}    ${10000000}

${MIN_GAIN}    ${0}
${MAX_GAIN}    ${150}

${MIN_INDEX}    ${1}
${MAX_INDEX}    ${4}


*** Test Cases ***

Set frequency
    Send command and check response    !freq\=${MIN_GAIN}    ${FIELD_FREQUENCY}=${MIN_GAIN}
    

Check if aliases are working
    [Template]    Send command and check response
    !g\=${MIN_GAIN}    ${True}
    !gain\=${MIN_GAIN}    ${True}
    get_gain\=${MIN_GAIN}    ${True}

    -    ${True}
    get_update    ${True}

    ?g    ${True}
    ?gain    ${True}
    get_gain    ${True}


Check if invalid syntax throws error
    [Template]    Send command and check response
    !gain\=-1000    ${False}
    !gain${MIN_INDEX}    ${False}
    !gain\=asdf    ${False}
    !gain\=${MIN_GAIN}    ${False}
    ?gain\=${MIN_GAIN}    ${False}
    ?gain${MIN_INDEX}    ${False}
    ?gainappendedtext    ${False}


Check limits of parameters
    [Template]    Send command and check response
    !gain\=${MAX_GAIN}    ${True}
    !gain\=${MIN_GAIN}    ${True}
    !gain\=${${MAX_GAIN} + 1}    ${False}
    !gain\=${${MIN_GAIN} - 1}    ${False}

    ?atf${MAX_INDEX}    ${True}
    ?atf${MIN_INDEX}    ${True}
    ?atf${${MAX_INDEX} + 1}    ${False}
    ?atf${${MIN_INDEX} - 1}    ${False}



Send Example Command
    [Tags]    expensive_to_run
    ${command_examples_list}=    RemoteController.Deduce list of command examples
    FOR  ${command_example}  IN  @{command_examples_list}
        Run Keyword and Continue on Failure    Send command and check if the device crashes    ${command_example} 
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
    
    
Send command and check if the device crashes
    [Arguments]    ${command_request}
    ${answer}=    RemoteController.Send Command     ${command_request}
    Log    Answer received: "${answer}[0]"
    Log    Is Answer Valid: "${answer}[2]"
    ${is_connected}=    RemoteController.Is connected to device
    Should Be True    ${is_connected}


Send command and check response
    [Arguments]    ${command_request}    ${should_be_valid}=${True}    &{expected_answer_values}
    ${answer}=    RemoteController.Send Command     ${command_request}
    Log    Answer received: "${answer}[0]"
    Should Be Equal    ${answer}[2]    ${should_be_valid}
    FOR  ${field_name}    ${expected_value}  IN  &{expected_answer_values}
        Should Be Equal    ${answer}[1][${field_name}]    ${expected_value}
    END
    
