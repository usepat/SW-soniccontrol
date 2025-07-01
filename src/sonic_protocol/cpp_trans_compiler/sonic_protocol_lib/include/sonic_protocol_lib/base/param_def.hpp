#pragma once
#include "sonic_protocol_lib/base/field_type_def.hpp"
#include "sonic_protocol_lib/base/code.hpp"
#include <string_view>

namespace sonic_protocol_lib {

enum class ParamType {
    SETTER,
    INDEX
};

struct ParamDef {
    FieldName_t field_name{FIELD_NAME_UNDEFINED};
    ParamType param_type {ParamType::SETTER};
    FieldTypeDef field_type;
};

}