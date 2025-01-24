*** Settings ***

Resource    ../keywords_gui.robot


*** Test Cases ***

Set gain over serial updates status bar
    Switch to tab "${SERIAL_MONITOR_TAB}"
    Gui.Set text of widget "${SERIAL_MONITOR_COMMAND_LINE_INPUT_ENTRY}" to "!gain=50"
    Gui.Press button "${SERIAL_MONITOR_SEND_BUTTON}"
    ${gain_label}=     Gui.Wait up to "1000" ms for the widget "${STATUS_BAR_GAIN_LABEL}" to change text
    Should Contain    ${gain_label}    50 %

Sending a command displays it in the monitor
    Switch to tab "${SERIAL_MONITOR_TAB}"
    ${command}=    Set Variable    ?info
    Gui.Set text of widget "${SERIAL_MONITOR_COMMAND_LINE_INPUT_ENTRY}" to "${command}"
    Gui.Press button "${SERIAL_MONITOR_SEND_BUTTON}"
    Gui.Let the app update for "1000" ms
    ${answer_str}=    Gui.Get text of "-1"th child of widget "${SERIAL_MONITOR_SCROLL_FRAME}"
    ${command_entry}=    Gui.Get text of "-2"th child of widget "${SERIAL_MONITOR_SCROLL_FRAME}"
    Should Contain    ${command_entry}    ${command}  
