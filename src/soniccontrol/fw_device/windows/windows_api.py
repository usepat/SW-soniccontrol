import ctypes
from ctypes import wintypes
from enum import Enum
from typing import Any, Generator



class GUID(ctypes.Structure):
    _fields_ = [
        ("Data1", wintypes.DWORD),
        ("Data2", wintypes.WORD),
        ("Data3", wintypes.WORD),
        ("Data4", ctypes.c_byte * 8),
    ]


class DEVPROPKEY(GUID):
    _fields_ = [*GUID._fields_, ("pid", wintypes.DWORD)]


class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("ClassGuid", GUID),
        ("DevInst", wintypes.DWORD),
        ("Reserved", ctypes.POINTER(ctypes.c_ulong)),
    ]


DEVINST = wintypes.DWORD

class PropType(Enum):
    STRING = 0x00000012
    STRING_LIST = 0x00001012
    RAW = 0


cfgmgr32 = ctypes.WinDLL("cfgmgr32")
setupapi = ctypes.WinDLL("setupapi")
advapi32 = ctypes.WinDLL("advapi32") 


DIGCF_PRESENT = 0x00000002
DIGCF_ALLCLASSES = 0x00000004

DIREG_DEV = 0x00000001
KEY_READ = 0x20019


DEVPKEY_Device_LocationInfo = DEVPROPKEY(
    Data1=0xa45c254e,
    Data2=0xdf1c,
    Data3=0x4efd,
    Data4=[0x80, 0x20, 0x67, 0xd1, 0x46, 0xa8, 0x50, 0xe0],
    pid=15
) 


def setup_di_get_device_property_w(device_info_set, device_info_data, prop_key):
    required_size = wintypes.DWORD(0)
    prop_type = wintypes.DWORD()

    # First call (expected to fail with insufficient buffer)
    res = setupapi.SetupDiGetDevicePropertyW(
        device_info_set,
        ctypes.byref(device_info_data),
        ctypes.byref(prop_key),
        ctypes.byref(prop_type),
        None,
        0,
        ctypes.byref(required_size),
        0
    )

    ERROR_INSUFFICIENT_BUFFER = 122

    if res == 0:
        err = ctypes.GetLastError()
        if err != ERROR_INSUFFICIENT_BUFFER:
            raise ctypes.WinError(err)

    buffer = (ctypes.c_byte * required_size.value)()

    # Second call (actual data)
    res = setupapi.SetupDiGetDevicePropertyW(
        device_info_set,
        ctypes.byref(device_info_data),
        ctypes.byref(prop_key),
        ctypes.byref(prop_type),
        ctypes.byref(buffer),
        required_size,
        None,
        0
    )

    if res == 0:
        raise ctypes.WinError(ctypes.GetLastError())

    return buffer, prop_type.value


def decode_property(buffer, prop_type: PropType):
    raw = bytes(buffer)

    if prop_type == PropType.STRING:
        return raw.decode("utf-16-le").rstrip("\x00")

    if prop_type == PropType.STRING_LIST:
        text = raw.decode("utf-16-le")
        return [s for s in text.split("\x00") if s]

    if prop_type == PropType.RAW:
        return raw
    
    assert False, "not implemented"


def iter_devices(device_info_set):
    index = 0
    device_info_data = SP_DEVINFO_DATA()
    device_info_data.cbSize = ctypes.sizeof(SP_DEVINFO_DATA)

    while True:
        res = setupapi.SetupDiEnumDeviceInfo(
            device_info_set,
            index,
            ctypes.byref(device_info_data)
        )
        if not res:
            break

        yield device_info_data
        index += 1


def get_devinst_from_instance_id(instance_id: str) -> DEVINST:
    devinst = DEVINST()

    res = cfgmgr32.CM_Locate_DevNodeW(
        ctypes.byref(devinst),
        ctypes.c_wchar_p(instance_id),
        0
    )

    if res != 0:
        raise RuntimeError(f"CM_Locate_DevNodeW failed: {res}")

    return devinst

def get_instance_id_from_devinst(devinst: DEVINST) -> str:
    buffer = ctypes.create_unicode_buffer(512)

    res = cfgmgr32.CM_Get_Device_IDW(
        devinst,
        buffer,
        len(buffer),
        0
    )

    if res != 0:
        raise RuntimeError(f"CM_Get_Device_IDW failed: {res}")

    return buffer.value

def get_parent_devinst(devinst: DEVINST) -> DEVINST | None:
    parent = DEVINST()

    res = cfgmgr32.CM_Get_Parent(
        ctypes.byref(parent),
        devinst,
        0
    )

    if res != 0:
        return None  # reached top

    return parent

def iter_ancestors_of_device(instance_id: DEVINST) -> Generator[DEVINST]:
    current_id = instance_id
    while True:
        yield current_id

        parent = get_parent_devinst(current_id)
        if parent is None:
            return

        current_id = parent


def is_usb_device(instance_id: DEVINST):
    id_str  = get_instance_id_from_devinst(instance_id)
    return id_str.startswith("USB\\VID_")

def get_usb_device_instance_id(instance_id: str | DEVINST) -> DEVINST | None:
    if isinstance(instance_id, str):
        instance_id = get_devinst_from_instance_id(instance_id)

    for ancestor_id in iter_ancestors_of_device(instance_id):
        if is_usb_device(ancestor_id):
            return ancestor_id
    return None

def get_device_info_set():
    device_info_set = setupapi.SetupDiGetClassDevsW(
        None,
        None,
        None,
        DIGCF_ALLCLASSES | DIGCF_PRESENT
    )

    if device_info_set == ctypes.c_void_p(-1).value:
        raise ctypes.WinError()
    return device_info_set

def get_device_property(instance_id: DEVINST, prop_key: DEVPROPKEY, prop_type: PropType) -> Any:
    device_info_set = get_device_info_set()
    
    for dev_info in iter_devices(device_info_set):
        if dev_info.DevInst != instance_id:
            continue

        value = setup_di_get_device_property_w(device_info_set, dev_info, prop_key)
        return decode_property(value, prop_type)
    
    assert False, "No device found with the given instance id"

def get_port_name_from_devinfo(device_info_set, dev_info):
    hkey = setupapi.SetupDiOpenDevRegKey(
        device_info_set,
        ctypes.byref(dev_info),
        0x00000001,  # DICS_FLAG_GLOBAL
        0,
        DIREG_DEV,
        KEY_READ
    )

    if hkey == wintypes.HANDLE(-1).value:
        return None

    try:
        value_name = ctypes.create_unicode_buffer("PortName")
        data = ctypes.create_unicode_buffer(256)
        data_size = wintypes.DWORD(ctypes.sizeof(data))

        res = advapi32.RegQueryValueExW(
            hkey,
            value_name,
            None,
            None,
            ctypes.byref(data),
            ctypes.byref(data_size)
        )

        if res != 0:
            return None

        return data.value

    finally:
        advapi32.RegCloseKey(hkey)

def get_physical_location_path_of_device(instance_id: str | DEVINST) -> str:
    usb_devinst = get_usb_device_instance_id(instance_id)
    assert usb_devinst is not None, "The device is not a usb device and has no ancestor that is that"

    location: str = get_device_property(usb_devinst, DEVPKEY_Device_LocationInfo, PropType.STRING)
    return location


def get_device_instance_id_from_com_port(com_port: str) -> DEVINST | None:
    # Note: for storage devices just use the pnp_device_id as instance id. 
    device_info_set = get_device_info_set()
    
    for dev_info in iter_devices(device_info_set):
        port_name: str | None = get_port_name_from_devinfo(device_info_set, dev_info)
        if port_name and port_name == com_port:
            return dev_info.DevInst
    
    return None

def is_there_usb_device_on_location(location: str) -> bool:
    device_info_set = get_device_info_set()
    
    for dev_info in iter_devices(device_info_set):
        if not is_usb_device(dev_info.DevInst):
            continue

        device_location: str = get_device_property(dev_info.DevInst, DEVPKEY_Device_LocationInfo, PropType.STRING)
        if device_location == location:
            return True
        
    return False
        

