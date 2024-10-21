#pragma once
#include "field_type_def.hpp"
#include <string_view>

namespace sonic::protocol_defs {

enum class ParamType {
    SETTER,
    INDEX
};

struct ParamDef {
    std::string_view name;
    ParamType param_type {ParamType::SETTER};
    FieldTypeDef field_type;
};

}