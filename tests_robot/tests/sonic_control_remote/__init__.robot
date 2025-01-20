*** Settings ***

Resource    keywords_remote_control.robot

Suite Setup    Connect to device
Suite Teardown    RemoteController.Disconnect

Test Setup    Reconnect if disconnected

