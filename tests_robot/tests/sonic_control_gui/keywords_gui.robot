*** Settings ***

Resource    ../variables.robot

Library    sonic_robot.RobotSonicControlGui    AS    Gui
Library    OperatingSystem

Variables    sonic_robot.variables
Variables    sonic_robot.labels


*** Variables ***

${TIMEOUT_CONNECTION_MS}    ${60000}


*** Keywords ***

Connect via url "${URL}"
    IF  $URL is None
        Fail    msg=No url was provieded
    END
    Gui.Set text of widget "${CONNECTION_PORTS_COMBOBOX}" to "${URL}"
    Gui.Press button "${CONNECTION_CONNECT_VIA_URL_BUTTON}"


Delete simulation memory file
    Remove File    ./fakeDataFram.bin


Open device window
    IF  '${SIMULATION_EXE_PATH}' == '' or '${SIMULATION_EXE_PATH}' == 'None'
        Set Suite Variable    ${SIMULATION_EXE_PATH}    %{SIMULATION_EXE_PATH}    # robotcode: ignore
    END
    Gui.Open app    ${SIMULATION_EXE_PATH}
    Gui.Let the app update for "500" ms

    IF  "${TARGET}" == "simulation"
        Delete simulation memory file
        Gui.Press button "${CONNECTION_CONNECT_TO_SIMULATION_BUTTON}"
    ELSE IF    "${TARGET}" == "url"
        Connect via url "${URL}"
    ELSE
        Fail    msg=The target specified is not valid: ${TARGET}
    END

    Gui.Wait up to "${TIMEOUT_CONNECTION_MS}" ms for the widget "${HOME_DEVICE_TYPE_LABEL}" to be registered
    Gui.Let the app update for "500" ms    # Ensure that stuff is loaded and initialized correctly


Send command "${COMMAND}" over serial monitor
    Gui.Set text of widget "${SERIAL_MONITOR_COMMAND_LINE_INPUT_ENTRY}" to "${COMMAND}"
    Gui.Press button "${SERIAL_MONITOR_SEND_BUTTON}"

    ${answer_str}=    Get answer of serial monitor

    RETURN    ${answer_str}

Get answer of serial monitor
    [Timeout]    5 s
    WHILE    True
        Gui.Let the app update for "500" ms
        ${loading_label}=    Gui.Get text of widget "${SERIAL_MONITOR_LOADING_LABEL}"
        IF       '${LABEL_WAITING_FOR_ANSWER}' in '${loading_label}'
            CONTINUE
        END

        ${answer_str}=    Gui.Get text of "-1"th child of widget "${SERIAL_MONITOR_SCROLL_FRAME}"
        RETURN    ${answer_str}
    END


Set device to default state
    Gui.Switch to tab "${SERIAL_MONITOR_TAB}"
    Gui.Let the app update for "200" ms
    Send command "!OFF" over serial monitor
    Send command "!freq=100000" over serial monitor
    Send command "!gain=100" over serial monitor
    Gui.Let the app update for "100" ms


Set ramp args
    Gui.Set text of widget "${PROC_CONTROLLING_PROCEDURE_COMBOBOX}" to "Ramp"
    Gui.Set text of widget "${RAMP_F_START}" to "100000"
    Gui.Set text of widget "${RAMP_F_STOP}" to "200000"
    Gui.Set text of widget "${RAMP_F_STEP}" to "10000"
    Gui.Set text of widget "${RAMP_T_ON_TIME}" to "500"
    Gui.Set text of widget "${RAMP_T_ON_UNIT}" to "ms"
    Gui.Set text of widget "${RAMP_T_OFF_TIME}" to "500"
    Gui.Set text of widget "${RAMP_T_OFF_UNIT}" to "ms"

Set spectrum measure args
    Gui.Set text of widget "${SPECTRUM_MEASURE_GAIN}" to "50"
    Gui.Set text of widget "${SPECTRUM_MEASURE_F_START}" to "100000"
    Gui.Set text of widget "${SPECTRUM_MEASURE_F_STOP}" to "105000"
    Gui.Set text of widget "${SPECTRUM_MEASURE_F_STEP}" to "1000"
    Gui.Set text of widget "${SPECTRUM_MEASURE_T_ON_TIME}" to "250"
    Gui.Set text of widget "${SPECTRUM_MEASURE_T_ON_UNIT}" to "ms"
    Gui.Set text of widget "${SPECTRUM_MEASURE_T_OFF_TIME}" to "250"
    Gui.Set text of widget "${SPECTRUM_MEASURE_T_OFF_UNIT}" to "ms"
    Gui.Set text of widget "${SPECTRUM_MEASURE_T_OFFSET_TIME}" to "500"
    Gui.Set text of widget "${SPECTRUM_MEASURE_T_OFFSET_UNIT}" to "ms"

