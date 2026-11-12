from typing import cast

from sonic_protocol.field_names import EFieldName
from sonic_protocol.protocols.protocol_v3_2_0.commands.commands import PluginVarType
from sonic_protocol.schema import Version
from soniccontrol.firmware_plugin_api.plugin_endpoints import FirmwarePluginEndpoints, VarDef, VarType
from soniccontrol.sonic_device import SonicDevice
from sonic_protocol import cmds


def convert_to_var_type(plugin_var_type: PluginVarType) -> type[VarType]:
    return {
        PluginVarType.UINT32: int,
        PluginVarType.FLOAT32: float,
        PluginVarType.BOOL: bool,
        PluginVarType.STR: str,
    }[plugin_var_type]


async def discover_firmware_plugins(device: SonicDevice) -> list[FirmwarePluginEndpoints]:
    plugins: list[FirmwarePluginEndpoints] = []

    answer = await device.execute_command(cmds.GetNumPlugins())
    num_plugins = cast(int, answer[EFieldName.COUNT])

    for plugin_index in range(num_plugins):
        answer = await device.execute_command(cmds.GetPluginInfo(plugin_index))
        plugin_name = cast(str, answer[EFieldName.NAME])
        version = cast(Version, answer[EFieldName.VERSION])
        num_variables = cast(int, answer[EFieldName.NUM_VARIABLES])
        num_actions  = cast(int, answer[EFieldName.NUM_ACTIONS])

        var_defs: dict[str, VarDef] = {}
        for var_index in range(num_variables):
            answer = await device.execute_command(cmds.GetPluginVarInfo(plugin_index, var_index))
            var_name = cast(str, answer[EFieldName.NAME])
            plugin_var_type = cast(PluginVarType, answer[EFieldName.TYPE])
            var_type = convert_to_var_type(plugin_var_type)
            is_writable = cast(bool, answer[EFieldName.IS_WRITABLE])

            var_defs[var_name] = VarDef(var_type, is_writable)

        action_names: list[str] = []
        for action_index in range(num_actions):
            answer = await device.execute_command(cmds.GetPluginActionInfo(plugin_index, action_index))
            action_names.append(answer[EFieldName.NAME])

        plugins.append(FirmwarePluginEndpoints(device, plugin_name, version, var_defs, action_names))

    return plugins
