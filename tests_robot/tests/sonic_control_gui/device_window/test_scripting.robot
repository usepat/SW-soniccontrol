*** Settings ***

Resource    ../keywords_gui.robot

Test Teardown    Set scripting tab to default state


*** Variables ***
${TEST_SCRIPT_HOLD}    
    ...    send "!ON"\n
    ...    hold 5s\n
    ...    send "!OFF"

    
*** Test Cases ***

Execute test script holds application
    Gui.Switch to tab "${SCRIPTING_TAB}"
    Gui.Set text of widget "${EDITOR_TEXT_EDITOR}" to "${TEST_SCRIPT_HOLD}"
    Gui.Press button "${EDITOR_START_PAUSE_CONTINUE_BUTTON}"
    
    # Shitty MessageBox appears, if you do not start a script over an experiment
    Gui.Wait up to "200" ms for the widget "${MESSAGE_BOX}" to be registered
    Gui.Press button "${MESSAGE_BOX_OPTION_PROCEED}"

    Gui.Let the app update for "4000" ms
    ${signal_text_after_4000ms}=     Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Gui.Let the app update for "4000" ms
    ${signal_text_after_8000ms}=     Gui.Get text of widget "${STATUS_BAR_SIGNAL_LABEL}"
    Should Contain    ${signal_text_after_4000ms}    ON
    Should Contain    ${signal_text_after_8000ms}    OFF


*** Keywords ***

Set scripting tab to default state
    ${start_stop_button_text}=    Gui.Get text of widget "${EDITOR_START_PAUSE_CONTINUE_BUTTON}"
    IF  "${start_stop_button_text}" != "${LABEL_START_LABEL}" 
        Gui.Press button "${EDITOR_STOP_BUTTON}"
    END
    Gui.Set text of widget "${EDITOR_TEXT_EDITOR}" to ""
