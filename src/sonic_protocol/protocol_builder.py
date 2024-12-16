
from copy import copy
import attrs
from typing import Dict, List, TypeVar
from sonic_protocol.python_parser.answer import AnswerValidator
from sonic_protocol.python_parser.answer_validator_builder import AnswerValidatorBuilder
from sonic_protocol.defs import AnswerDef, CommandCode, CommandContract, CommandDef, DeviceParamConstantType, DeviceParamConstants, DeviceType, FieldType, MetaExport, Protocol, UserManualAttrs, Version


@attrs.define()
class CommandLookUp:
    command_def: CommandDef = attrs.field()
    answer_def: AnswerDef = attrs.field() # probably not needed, we leave it anyway here
    answer_validator: AnswerValidator = attrs.field()
    user_manual_attrs: UserManualAttrs = attrs.field(default=UserManualAttrs())
    tags: List[str] = attrs.field(default=[])

T = TypeVar("T")
CommandLookUpTable = Dict[CommandCode, CommandLookUp]
class ProtocolBuilder:
    def __init__(self, protocol: Protocol):
        self._protocol = protocol

    def build(self, device_type: DeviceType, version: Version, release: bool) -> CommandLookUpTable:
        lookups: Dict[CommandCode, CommandLookUp] = {}

        if version > self._protocol.version:
            # TODO: how to react if version is higher?
            # log? warn? error?
            pass

        consts = self._filter_exports(self._protocol.consts, version, device_type)

        for export in self._protocol.commands:
            if not export.descriptor.is_valid(version, device_type):
                continue

            commands: List[CommandContract] = export.exports if isinstance(export.exports, list) else [export.exports]
            for command in commands:
                if release and not command.is_release:
                    continue
                lookups[command.code] = self._extract_command_lookup(command, consts, version, device_type)

        return lookups


    def _extract_command_lookup(self, command: CommandContract, consts: DeviceParamConstants, version: Version, device_type: DeviceType) -> CommandLookUp:
        command_def = self._filter_exports(command.command_defs, version, device_type)
        command_def = self._extract_prot_specific_attrs(command_def, version, device_type)
        if command_def.index_param is not None:
            command_def.index_param.param_type = self._adjust_field_type_according_to_constraints(command_def.index_param.param_type, consts)
        if command_def.setter_param is not None:
            command_def.setter_param.param_type = self._adjust_field_type_according_to_constraints(command_def.setter_param.param_type, consts)

        answer_def = self._filter_exports(command.answer_defs, version, device_type)
        answer_def = self._extract_prot_specific_attrs(answer_def, version, device_type)
        answer_def.fields = list(map(lambda field: self._filter_exports(field, version, device_type), answer_def.fields))
        for field in answer_def.fields:
            field.field_type = self._adjust_field_type_according_to_constraints(field.field_type, consts)

        user_manual_attrs = self._filter_exports(command.user_manual_attrs, version, device_type)
        validator = AnswerValidatorBuilder().create_answer_validator(answer_def)
        
        return CommandLookUp(
            command_def,
            answer_def,
            validator,
            user_manual_attrs,
            command.tags
        )
    
    def _adjust_field_type_according_to_constraints(self, field_type: FieldType, consts: DeviceParamConstants) -> FieldType:
        updated_field_type = copy(field_type)
        if isinstance(field_type.min_value, DeviceParamConstantType):
            updated_field_type.min_value = getattr(consts, field_type.min_value.value)
        if isinstance(field_type.max_value, DeviceParamConstantType):
            updated_field_type.max_value = getattr(consts, field_type.max_value.value)
        return updated_field_type

    def _extract_prot_specific_attrs(self, obj: T, version: Version, device_type: DeviceType) -> T:
        modified_obj = copy(obj)
        attrs_fields = [
            "user_manual_attrs",
            "sonic_text_attrs"
        ]
        for field in attrs_fields:
            if not hasattr(modified_obj, field):
                attr_export_list = getattr(modified_obj, field)
                export = self._filter_exports(attr_export_list, version, device_type)
                setattr(modified_obj, field, export)
        return modified_obj

    def _filter_exports(self, defs: T | List[MetaExport[T]], version: Version, device_type: DeviceType) -> T:
        if not isinstance(defs, list):
            return defs
        for def_entry in defs:
            if def_entry.descriptor.is_valid(version, device_type):
                return def_entry.exports
        raise LookupError(f"There was no definition exported for the combination of version {version} and type {device_type}")
    