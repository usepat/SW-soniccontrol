@defgroup PicoDeviceDetection
@ingroup SonicControl
@addtogroup PicoDeviceDetection
@{

# Pico Device Detection

The Device detection is used to find plugged in pico devices, so that we can flash them with the new firmware. For this pyudev is used a python implementation of the udev linux system library.  
udev detects all devices, where devices can be sub devices of others. There is a hierarchical pattern for example: A partition is a subdevice of a block device which in turn is a sub device of a usb device.  
This hierarchical pattern allows us to filter out pico devices. As we search for usb devices that are from the Raspberry Pi company and have the correct product name.  
When the pico is plugged in it is either a mass storage device, if it is in bootmode or else a serial device that can be communicated with (tty).  
In the later case we have to force the pico to go into bootmode, so that we can flash it over usb. If uart flashing is available, we can use our own bios to flash it. 

@startuml
!include soniccontrol/class_pico_devcie_detection.puml
@enduml

@}
