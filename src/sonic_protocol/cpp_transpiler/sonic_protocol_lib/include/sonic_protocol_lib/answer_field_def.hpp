#pragma once
#include "field_type_def.hpp"
#include "field_names.hpp"
#include <string_view>

namespace sonic_protocol_lib {

using FieldPath = std::initializer_list<FieldName_t>;

struct AnswerFieldDef {
    FieldPath path {{}};
    FieldTypeDef type;
    std::string_view prefix {""};
    std::string_view postfix {""};
};

}