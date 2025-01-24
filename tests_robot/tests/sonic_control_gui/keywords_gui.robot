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
    IF  ${SIMULATION_EXE_PATH} is None
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
    Gui.Let the app update for "500" ms


Set device to default state
    Send command "!OFF" over serial monitor
    Send command "!freq=100000" over serial monitor
    Send command "!gain=100" over serial monitor
    Gui.Let the app update for "100" ms