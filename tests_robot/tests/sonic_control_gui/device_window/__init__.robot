*** Settings ***
Resource    ../keywords_gui.robot


Suite Setup    Open device window
Suite Teardown    Close and clean up

Test Setup    Set device to default state
