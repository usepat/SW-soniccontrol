*** Settings ***

Resource    keywords_gui.robot

*** Test Cases ***

Check MessageBox pops up on disconnect
    Open device window
    Gui.Switch to tab "${HOME_TAB}"
    Gui.Press button "${HOME_DISCONNECT_BUTTON}"
    Gui.Wait up to "500" ms for the widget "${MESSAGE_BOX}" to be registered
    Gui.Press button "${MESSAGE_BOX_OPTION_OK}"    # closes the message box and the window
    [Teardown]
    Gui.Close app