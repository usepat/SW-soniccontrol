#pragma once
#include "sonic_protocol_lib/base/field_type_def.hpp"
#include "sonic_protocol_lib/base/code.hpp"
#include <string_view>

namespace sonic_protocol_lib {


struct AnswerFieldDef {
    FieldName_t name{0};
    FieldTypeDef type;
    std::string_view prefix {""};
    std::string_view postfix {""};
};

}