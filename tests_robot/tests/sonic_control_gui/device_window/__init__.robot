*** Settings ***
Resource    ../keywords_gui.robot


Suite Setup    Open device window
Suite Teardown    Gui.Close app

Test Setup    Set device to default state
