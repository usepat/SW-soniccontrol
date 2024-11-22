#pragma once
#include "field_type_def.hpp"
#include "field_names.hpp"
#include <string_view>

namespace sonic_protocol_lib {

enum class ParamType {
    SETTER,
    INDEX
};

struct ParamDef {
    FieldName field_name{FieldName::UNKNOWN_ANSWER};
    ParamType param_type {ParamType::SETTER};
    FieldTypeDef field_type;
};

}