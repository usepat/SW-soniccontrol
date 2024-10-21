#pragma once
#include "field_type_def.hpp"
#include <string_view>

namespace sonic::protocol_defs {

using FieldName_UnderlyingType = int16_t;
using FieldPath = std::initializer_list<FieldName_UnderlyingType>;

struct AnswerFieldDef {
    FieldPath path {{}};
    FieldTypeDef type;
    std::string_view prefix {""};
    std::string_view postfix {""};
};

}