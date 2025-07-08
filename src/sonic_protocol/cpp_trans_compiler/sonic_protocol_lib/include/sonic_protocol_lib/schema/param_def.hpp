#pragma once
#include "sonic_protocol_lib/schema/field_type_def.hpp"
#include "sonic_protocol_lib/schema/code.hpp"
#include <string_view>

namespace sonic_protocol_lib {

enum class ParamType {
    SETTER,
    INDEX
};

struct ParamDef {
    FieldName_t field_name{0};
    ParamType param_type {ParamType::SETTER};
    FieldTypeDef field_type;
};

}