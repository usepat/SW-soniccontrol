*** Settings ***
Resource    ../keywords_gui.robot

*** Variables ***

${TIMEOUT_MS}    ${10000}


*** Test Cases ***

Set frequency over home tab updates status bar
    [Tags]    -descaler
    Gui.Switch to tab "${HOME_TAB}"
    Gui.Set text of widget "${HOME_FREQUENCY_ENTRY}" to "200000"
    Gui.Press button "${HOME_SEND_BUTTON}"
    ${freq_label}=     Gui.Wait up to "${TIMEOUT_MS}" ms for the widget "${STATUS_BAR_FREQ_LABEL}" to change text
    Should Contain    ${freq_label}    200000 Hz    

Set gain over serial updates status bar
    [Tags]    -descaler
    Gui.Switch to tab "${SERIAL_MONITOR_TAB}"
    Send command "!gain=50" over serial monitor
    ${gain_label}=     Gui.Wait up to "${TIMEOUT_MS}" ms for the widget "${STATUS_BAR_GAIN_LABEL}" to change text
    Should Contain    ${gain_label}    50 %    
