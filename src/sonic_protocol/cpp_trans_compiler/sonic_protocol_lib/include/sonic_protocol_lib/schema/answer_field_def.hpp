#pragma once
#include "sonic_protocol_lib/schema/field_type_def.hpp"
#include "sonic_protocol_lib/schema/code.hpp"
#include <string_view>

namespace sonic_protocol_lib {


struct AnswerFieldDef {
    FieldName_t name{0};
    FieldTypeDef type;
    std::string_view prefix {""};
    std::string_view postfix {""};
};

}