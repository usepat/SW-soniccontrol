*** Settings ***

Library    sonic_robot.RobotSonicControlGui    AS    Gui
Library    OperatingSystem

Variables    sonic_robot.variables
Variables    sonic_robot.labels

Suite Setup    Open device window
Suite Teardown    Gui.Close app

Test Setup    Set device to default state

Keyword Tags    descaler    mvp_worker



*** Variables ***

${TARGET}    simulation    # can be either "simulation" or "url"
${SIMULATION_EXE_PATH}    ${None}
${URL}    ${None}

${TIMEOUT_CONNECTION_MS}    ${60000}
${TIMEOUT_MS}    ${10000}

${TEST_SCRIPT_HOLD}    
    ...    !ON\n
    ...    hold 5s\n
    ...    !OFF



*** Test Cases ***

Set frequency over home tab updates status bar
    [Tags]    -descaler
    Gui.Set text of widget "${HOME_FREQUENCY_ENTRY}" to "200000"
    Gui.Press button "${HOME_SEND_BUTTON}"
    ${freq_label}=     Gui.Wait up to "${TIMEOUT_MS}" ms for the widget "${STATUS_BAR_FREQ_LABEL}" to change text
    Should Contain    ${freq_label}    200    # TODO: use a better check

Set gain over serial updates status bar
    [Tags]    -descaler
    Send command "!gain=50" over serial monitor
    ${gain_label}=    Gui.Get text of widget "${STATUS_BAR_GAIN_LABEL}"
    Should Contain    ${gain_label}    50    # TODO: use a better check

Execute test script holds application
    Gui.Set text of widget "${EDITOR_TEXT_EDITOR}" to "${TEST_SCRIPT_HOLD}"
    Gui.Press button "${EDITOR_START_PAUSE_CONTINUE_BUTTON}"
    Gui.Let the app run free for "500" ms
    ${signal_text_after_500ms}=    Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Gui.Let the app run free for "4000" ms
    ${signal_text_after_4500ms}=     Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Gui.Let the app run free for "1000" ms
    ${signal_text_after_5500ms}=     Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Should Contain    ${signal_text_after_500ms}    ON
    Should Contain    ${signal_text_after_4500ms}    ON
    Should Contain    ${signal_text_after_5500ms}    OFF
    [Teardown]
    Set scripting tab to default state



*** Keywords ***

# TODO: This has to be tested
Connect via url "${URL}"
    IF  ${URL} is None
        Fail    msg=No url was provieded
    END
    Gui.Set text of widget "${CONNECTION_PORTS_COMBOBOX}" to "${URL}"
    Gui.Press button "${CONNECTION_CONNECT_VIA_URL_BUTTON}"


Delete simulation memory file
    Remove File    ./fakeDataFram.bin


Open device window
    IF  ${SIMULATION_EXE_PATH} is None
        Set Suite Variable    ${SIMULATION_EXE_PATH}    %{SIMULATION_EXE_PATH}    # robotcode: ignore
    END
    Gui.Open app    ${SIMULATION_EXE_PATH}

    IF  "${TARGET}" == "simulation"
        Delete simulation memory file
        Gui.Press button "${CONNECTION_CONNECT_TO_SIMULATION_BUTTON}"
    ELSE IF    "${TARGET}" == "url"
        Connect via url "${URL}"
    ELSE
        Fail    msg=The target specified is not valid: ${TARGET}
    END

    Gui.Wait up to "${TIMEOUT_CONNECTION_MS}" ms for the widget "${HOME_DEVICE_TYPE_LABEL}" to be registered
    Gui.Let the app run free for "5000" ms    # Ensure that stuff is loaded and initialized correctly


Send command "${COMMAND}" over serial monitor
    Gui.Set text of widget "${SERIAL_MONITOR_COMMAND_LINE_INPUT_ENTRY}" to "${COMMAND}"
    Gui.Press button "${SERIAL_MONITOR_SEND_BUTTON}"
    Gui.Let the app run free for "500" ms


Set device to default state
    Send command "!OFF" over serial monitor
    Send command "!freq=100000" over serial monitor
    Send command "!gain=100" over serial monitor


Set scripting tab to default state
    ${start_stop_button_text}=    Gui.Get text of widget "${EDITOR_START_PAUSE_CONTINUE_BUTTON}"
    IF  "${start_stop_button_text}" != "${LABEL_START_LABEL}" 
        Gui.Press button "${EDITOR_STOP_BUTTON}"
    END
    Gui.Set text of widget "${EDITOR_TEXT_EDITOR}" to ""
