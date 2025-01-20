*** Settings ***

Resource    ../keywords_gui.robot

*** Variables ***
${TEST_SCRIPT_HOLD}    
    ...    !ON\n
    ...    hold 5s\n
    ...    !OFF

*** Test Cases ***

Execute test script holds application
    Gui.Switch to tab "${SCRIPTING_TAB}"
    Gui.Set text of widget "${EDITOR_TEXT_EDITOR}" to "${TEST_SCRIPT_HOLD}"
    Gui.Press button "${EDITOR_START_PAUSE_CONTINUE_BUTTON}"
    Gui.Let the app update for "500" ms
    ${signal_text_after_500ms}=    Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Gui.Let the app update for "4000" ms
    ${signal_text_after_4500ms}=     Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Gui.Let the app update for "1000" ms
    ${signal_text_after_5500ms}=     Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Should Contain    ${signal_text_after_500ms}    ON
    Should Contain    ${signal_text_after_4500ms}    ON
    Should Contain    ${signal_text_after_5500ms}    OFF
    [Teardown]
    Set scripting tab to default state
    


*** Keywords ***


Set scripting tab to default state
    ${start_stop_button_text}=    Gui.Get text of widget "${EDITOR_START_PAUSE_CONTINUE_BUTTON}"
    IF  "${start_stop_button_text}" != "${LABEL_START_LABEL}" 
        Gui.Press button "${EDITOR_STOP_BUTTON}"
    END
    Gui.Set text of widget "${EDITOR_TEXT_EDITOR}" to ""