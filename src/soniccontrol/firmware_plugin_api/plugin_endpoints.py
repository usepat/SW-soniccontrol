from typing import Any, cast
import attrs

from sonic_protocol.field_names import EFieldName
from sonic_protocol.schema import Version
from soniccontrol.sonic_device import SonicDevice
from sonic_protocol.python_parser import commands as cmds


VarType = int | float | bool | str

@attrs.define()
class VarDef:
    var_type: type[VarType]
    is_writable: bool


class FirmwarePluginEndpoints:
    def __init__(self, device: SonicDevice, plugin_name: str, version: Version, 
                 var_defs: dict[str, VarDef], action_defs: list[str]):
        self._device = device
        self._plugin_name = plugin_name
        self._version = version
        self._var_defs = var_defs
        self._action_defs = action_defs

    @property
    def version(self):
        return self._version

    @property
    def var_defs(self):
        return self._var_defs

    @property
    def action_defs(self):
        return self._action_defs

    async def fetch_var(self, var_name: str):
        if var_name not in self._var_defs:
            raise KeyError(f"var with name '{var_name}' is not known for plugin '{self._plugin_name}'")
        
        var_def = self._var_defs[var_name]
        type_to_class_map = {
            int: cmds.GetPluginVarUint,
            float: cmds.GetPluginVarBool,
            bool: cmds.GetPluginVarBool,
            str: cmds.GetPluginVarStr
        }

        cmd_class = type_to_class_map[var_def.var_type]
        cmd = cmd_class(self._plugin_name, var_name)
        answer = await self._device.execute_command(cmd, raise_exception=True, disconnect_on_exception=False)
        value = answer[EFieldName.VALUE]
        return value

    async def fetch_vars(self):
        for var_name in self._var_defs:
            await self.fetch_var(var_name)

    async def assign_var(self, var_name: str, value: VarType) -> None:
        if var_name not in self._var_defs:
            raise KeyError(f"var with name '{var_name}' is not known for plugin '{self._plugin_name}'")

        var_def = self._var_defs[var_name]
        var_type = var_def.var_type
        if not isinstance(value, var_type):
            raise TypeError(f"var is of type {var_type}, but value is of type {type(value)}")

        if not var_def.is_writable:
            raise PermissionError(f"Variable '{var_name}' is not writable")

        if isinstance(value, bool):
            cmd = cmds.SetPluginVarBool(self._plugin_name, var_name, value)
        elif isinstance(value, float):
            cmd = cmds.SetPluginVarFloat(self._plugin_name, var_name, value)
        elif isinstance(value, int):
            cmd = cmds.SetPluginVarUint(self._plugin_name, var_name, value)
        else:
            raise NotImplementedError("Setting plugin string vars is not supported yet")

        await self._device.execute_command(cmd, raise_exception=True, disconnect_on_exception=False)

    async def do_action(self, action_name: str) -> int:
        if action_name not in self._action_defs:
            raise KeyError(f"action with name '{action_name}' is not known for plugin '{self._plugin_name}'")
        
        cmd = cmds.DoPluginAction(self._plugin_name, action_name)
        answer = await self._device.execute_command(cmd,  raise_exception=True, disconnect_on_exception=False)
        error_code = cast(int, answer[EFieldName.ERROR_CODE])
        return error_code
