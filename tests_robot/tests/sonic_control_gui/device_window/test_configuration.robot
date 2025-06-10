*** Settings ***
Library    OperatingSystem

Resource    ../keywords_gui.robot

Test Teardown    Set configuration tab to default

*** Variables ***

${CONFIGURATION_TIME}    5000

${ATF_1}    200000
${ATK_1}    10.0
${ATT_1}    21.0

${INIT_SCRIPT}
    ...    frequency 690420\n
    ...    gain 10\n

${INIT_SCRIPT_PATH}    ./output/init_script_test.sonic

*** Test Cases ***

Send atf configs to device
    Gui.Switch to tab "${CONFIGURATION_TAB}"
    
    Gui.Set text of widget "${CONFIGURATION_AT_CONFIG_1_ATF_ENTRY}" to "${ATF_1}"
    Gui.Set text of widget "${CONFIGURATION_AT_CONFIG_1_ATK_ENTRY}" to "${ATK_1}"
    Gui.Set text of widget "${CONFIGURATION_AT_CONFIG_1_ATT_ENTRY}" to "${ATT_1}"
    Gui.Press button "${CONFIGURATION_SUBMIT_CONFIG_BUTTON}"
    Gui.Let the app update for "${CONFIGURATION_TIME}" ms

    Gui.Switch to tab "${SERIAL_MONITOR_TAB}"
    ${answer_atf}=    Send command "?atf1" over serial monitor
    ${answer_atk}=    Send command "?atk1" over serial monitor
    ${answer_att}=    Send command "?att1" over serial monitor

    Should Contain    ${answer_atf}    ${ATF_1} Hz
    Should Contain    ${answer_atk}    ${ATK_1}
    Should Contain    ${answer_att}    ${ATT_1}


Configure device with init script
    Gui.Switch to tab "${CONFIGURATION_TAB}"
    Create File    ${INIT_SCRIPT_PATH}    ${INIT_SCRIPT}
    File Should Exist    ${INIT_SCRIPT_PATH}
    ${absolute_path}=    Join Path    ${CURDIR}/../../../..   ${INIT_SCRIPT_PATH}
    ${absolute_path}=    Normalize Path    ${absolute_path}
    
    Gui.Set text of widget "${CONFIGURATION_BROWSE_FILES_ENTRY}" to "${absolute_path}"
    Gui.Press button "${CONFIGURATION_SUBMIT_CONFIG_BUTTON}"
    
    
    ${labels_status_bar}=    Create List    ${STATUS_BAR_GAIN_LABEL}    ${STATUS_BAR_FREQ_LABEL}
    ${changed_texts}=    Gui.Wait up to "${CONFIGURATION_TIME}" ms for multiple widgets "@{labels_status_bar}" to change text

    Should Be Equal As Strings    ${changed_texts["${STATUS_BAR_FREQ_LABEL}"]}    Frequency: 690420 Hz
    Should Be Equal As Strings    ${changed_texts["${STATUS_BAR_GAIN_LABEL}"]}    Gain: 10 %
    

*** Keywords ***

Set configuration tab to default
    Gui.Set text of widget "${CONFIGURATION_AT_CONFIG_1_ATF_ENTRY}" to "0"
    Gui.Set text of widget "${CONFIGURATION_AT_CONFIG_1_ATK_ENTRY}" to "0"
    Gui.Set text of widget "${CONFIGURATION_AT_CONFIG_1_ATT_ENTRY}" to "0"
    Gui.Set text of widget "${CONFIGURATION_BROWSE_FILES_ENTRY}" to ""
    Gui.Press button "${CONFIGURATION_SUBMIT_CONFIG_BUTTON}"
    Gui.Let the app update for "2000" ms



