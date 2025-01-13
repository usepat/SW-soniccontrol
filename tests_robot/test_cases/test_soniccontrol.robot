*** Settings ***
Library    sonic_robot.RobotRemoteController    log_path=${OUTPUT_DIR}    AS    RemoteController
Library    sonic_robot.conversion_utils

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

${MIN_SWF}    ${0}
${MAX_SWF}    ${15}

${MIN_GAIN}    ${0}
${MAX_GAIN}    ${150}

${MIN_INDEX}    ${1}
${MAX_INDEX}    ${4}


*** Test Cases ***

Test if commands are not being cutted off
    [Setup]    RemoteController.Send Command     !log[global]=DEBUG
    [Teardown]    RemoteController.Send Command     !log[global]=ERROR
    FOR    ${i}    IN RANGE    0    30
        Send command and check response    !ramp_f_start\=100000    should_be_valid=${True}    ${FIELD_RAMP_F_START}=${100000}
    END 


Set frequency
    [Tags]    -descaler
    Send command and check response    !freq\=${MIN_FREQUENCY}    ${FIELD_FREQUENCY}=${MIN_FREQUENCY}
    

Check if aliases are working
    [Template]    Send command and check response
    !g\=${MIN_GAIN}    ${True}
    !gain\=${MIN_GAIN}    ${True}
    set_gain\=${MIN_GAIN}    ${True}

    -    ${True}
    get_update    ${True}

    ?g    ${True}
    ?gain    ${True}
    get_gain    ${True}


Check if invalid syntax throws error
    [Template]    Send command and check response
    !gain\=-1000    ${False}
    !gain\=    ${False}
    !gain${MIN_INDEX}    ${False}
    !gain    ${False}
    !gain\=asdf    ${False}
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


Check basic setter commands are working
    [Tags]    -descaler
    [Template]    Send command and check response
    !ON
    !OFF
    !gain\=100
    !frequency\=${MIN_FREQUENCY}

    !att4\=${0}
    !atk1\=${100}
    !atf2\=${MIN_FREQUENCY}

    !wipe_f_step\=${MIN_FREQUENCY}
    !wipe_t_on\=${100}
    !scan_f_step\=${1000}
    !ramp_f_start\=${MIN_FREQUENCY}
    !tune_f_step\=${1000}


Test if gain set by setter can be retrieved with getter
    Send Command And Check Response    !gain\=${MIN_GAIN}
    Send Command And Check Response    ?gain    ${FIELD_GAIN}=${MIN_GAIN}
    Send Command And Check Response    !gain\=${MAX_GAIN}
    Send Command And Check Response    ?gain    ${FIELD_GAIN}=${MAX_GAIN}

Test if freq set by setter can be retrieved with getter
    [Tags]    -descaler
    Send Command And Check Response    !freq\=${MIN_FREQUENCY}
    Send Command And Check Response    ?freq    ${FIELD_FREQUENCY}=${MIN_FREQUENCY}
    Send Command And Check Response    !freq\=${MAX_FREQUENCY}
    Send Command And Check Response    ?freq    ${FIELD_FREQUENCY}=${MAX_FREQUENCY}

    Send Command And Check Response    !atf${MIN_INDEX}\=${MIN_FREQUENCY}
    Send Command And Check Response    ?atf${MIN_INDEX}    ${FIELD_ATF}=${MIN_FREQUENCY}
    Send Command And Check Response    !atf${MIN_INDEX}\=${MAX_FREQUENCY}
    Send Command And Check Response    ?atf${MIN_INDEX}    ${FIELD_ATF}=${MAX_FREQUENCY}

Test if swf set by setter can be retrieved with getter
    [Tags]    descaler    -worker
    Send Command And Check Response    !swf\=${MIN_SWF}
    Send Command And Check Response    ?swf    ${FIELD_SWF}=${MIN_SWF}
    Send Command And Check Response    !swf\=${MAX_SWF}
    Send Command And Check Response    ?swf    ${FIELD_SWF}=${MAX_SWF}

Test if input source can be set, if analog is set
    [Tags]    -worker    descaler
    [Teardown]    Reconnect
    ${EXPECTED_INPUT_SOURCE}=    Convert to input source    ANALOG
    Send command and check response    !input_source\=analog    ${FIELD_INPUT_SOURCE}=${EXPECTED_INPUT_SOURCE}
    ${EXPECTED_INPUT_SOURCE}=    Convert to input source    EXTERNAL
    Send command and check response    !input_source\=external    ${FIELD_INPUT_SOURCE}=${EXPECTED_INPUT_SOURCE}


Check procedure command returns error, if ramp_f_start and ramp_f_stop are the same
    [Tags]    -descaler
    [Setup]    Set Ramp Args
    [Teardown]    RemoteController.Send Command    !stop
    Send Command And Check Response    !ramp_f_start\=${100100}
    Send Command And Check Response    !ramp_f_stop\=${100100}
    Send command and check response    !ramp    ${False}

Check setter commands get blocked during procedure run
    [Tags]    -descaler
    [Setup]    Set Ramp Args
    [Teardown]   RemoteController.Send Command    !stop
    ${EXPECTED_PROCEDURE}=    Convert to procedure    RAMP
    Send command and check response    !ramp    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}
    Sleep    300ms
    Send command and check response    !freq\=${MIN_FREQUENCY}    ${False}

Check getter commands are allowed during procedure run
    [Tags]    -descaler
    [Setup]    Set Ramp Args
    [Teardown]    RemoteController.Send Command    !stop
    ${EXPECTED_PROCEDURE}=    Convert to procedure    RAMP
    Send command and check response    !ramp    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}
    Sleep    300ms
    Send command and check response    ?freq    ${True}


Test Stop turns off procedure
    [Tags]    -descaler
    [Setup]    Set Ramp Args
    [Teardown]    RemoteController.Send Command    !stop
    ${EXPECTED_PROCEDURE}=    Convert to procedure    RAMP
    Send command and check response    !ramp    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}
    Sleep    300ms
    ${EXPECTED_PROCEDURE}=    Convert to procedure    NO_PROC
    Send command and check response    !stop    ${True}    ${FIELD_PROCEDURE}=${EXPECTED_PROCEDURE}

Send Example Commands
    [Tags]    expensive_to_run
    ${command_examples_list}=    RemoteController.Deduce list of command examples
    ${num_iterations} =    Get Length    ${command_examples_list}
    FOR  ${i}    ${command_example}  IN ENUMERATE    @{command_examples_list}
        Run Keyword and Continue on Failure    Send command and check if the device crashes    ${command_example} 
        Run Keyword and Continue on Failure    RemoteController.Send Command    !stop
        Run Keyword and Continue on Failure    RemoteController.Send Command    !input_source=external
        Reconnect if disconnected
        Log To Console    Progress: Completed ${${i} + 1}/${num_iterations} iterations
    END


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

Set Ramp Args
    [Arguments]    ${f_start}=100000    ${f_stop}=110000    ${f_step}=1000    ${t_on}=100    ${t_off}=0
    Send Command And Check Response    !ramp_f_start\=${f_start}
    Send Command And Check Response    !ramp_f_stop\=${f_stop}
    Send Command And Check Response    !ramp_f_step\=${f_step}
    Send Command And Check Response    !ramp_t_on\=${t_on}
    Send Command And Check Response    !ramp_t_off\=${t_off} 
