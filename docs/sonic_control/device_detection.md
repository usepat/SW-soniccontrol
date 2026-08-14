@defgroup device_detection
@ingroup SonicControl
@addtogroup device_detection
@{

# Device Detection

## Requirements

Before soniccontrol can connect to a device it has first to detect them.  
Possible defices can be connected via usb or serial. They can be empty (not flashed) and appear as a disk in bootmode.  
Also when we want to restart a device (for example to start another application), it will disconnect and then get reenumerated by the OS, possibly under a new port.  

## Implementation

We created a `DeviceDiscovery` interface and several implementations for it for Linux, Windows and devices connected on a remote server. It offers functions for listing enumerated devices and redetection (waits until device disconnects and then reconnects).  
Also in `SonicDevice` a `restart` function was added, so that we can gracefully restart the device with proper error handling.  

For linux pyudev is used. It is a python implementation of the udev linux system library.  
udev detects all devices, where devices can be sub devices of others. There is a hierarchical pattern for example: A partition is a subdevice of a block device which in turn is a sub device of a usb device.  
This hierarchical pattern allows us to filter out pico devices. As we search for usb devices that are from the Raspberry Pi company and have the correct product name.  
When the pico is plugged in it is either a mass storage device, if it is in bootmode or else a serial device that can be communicated with (tty).  
In the later case we have to force the pico to go into bootmode, so that we can flash it over usb. If uart flashing is available, we can use our own bios to flash it. The flashing tools for this are implemented as plugin in the firmware repo.

For windows the `win api` is used and it is horrible to work with. Just inform yourself about it via the official docs.  

@startuml
!include soniccontrol/class_pico_devcie_detection.puml
@enduml
    


@}