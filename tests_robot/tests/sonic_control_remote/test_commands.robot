*** Settings ***

Resource    keywords_remote_control.robot

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect

Test Setup    Reconnect if disconnected

*** Variables ***

${MIN_FREQUENCY}    ${100000}
${MAX_FREQUENCY}    ${10000000}

${MIN_GAIN}    ${0}
${MAX_GAIN}    ${150}

${MIN_INDEX}    ${1}
${MAX_INDEX}    ${4}

*** Test Cases ***

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
    [Tags]    worker
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
    [Tags]    worker
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
    [Tags]    worker
    Send Command And Check Response    !freq\=${MIN_FREQUENCY}
    Send Command And Check Response    ?freq    ${FIELD_FREQUENCY}=${MIN_FREQUENCY}
    Send Command And Check Response    !freq\=${MAX_FREQUENCY}
    Send Command And Check Response    ?freq    ${FIELD_FREQUENCY}=${MAX_FREQUENCY}

    Send Command And Check Response    !atf${MIN_INDEX}\=${MIN_FREQUENCY}
    Send Command And Check Response    ?atf${MIN_INDEX}    ${FIELD_ATF}=${MIN_FREQUENCY}
    Send Command And Check Response    !atf${MIN_INDEX}\=${MAX_FREQUENCY}
    Send Command And Check Response    ?atf${MIN_INDEX}    ${FIELD_ATF}=${MAX_FREQUENCY}

Send Example Commands
    [Tags]    expensive_to_run
    #[Timeout]   1 minutes
    ${command_examples_list}=    RemoteController.Deduce list of command examples
    IF    "${TARGET}" != 'simulation'
        Remove Values From List    ${command_examples_list}    !FLASH_USB    !FLASH_UART_SLOW    !FLASH_UART_FAST
    END
    ${num_iterations} =    Get Length    ${command_examples_list}
    FOR  ${i}    ${command_example}  IN ENUMERATE    @{command_examples_list}
        IF     ${i} >= 0   #So we can skip commands, used for debugging
            Run Keyword and Continue on Failure    Send command and check if the device crashes    ${command_example} 
            Run Keyword and Continue on Failure    RemoteController.Send Command    !log[global]=ERROR
            Run Keyword and Continue on Failure    RemoteController.Send Command    !stop
            Run Keyword and Continue on Failure    RemoteController.Send Command    !input_source=external
            Reconnect if disconnected
            Log To Console    Progress: Completed ${${i} + 1}/${num_iterations} iterations
        ELSE
            Log To Console    Progress: Skip ${${i} + 1}/${num_iterations} iterations
        END
    END
