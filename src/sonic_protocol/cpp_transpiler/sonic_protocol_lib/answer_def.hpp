#pragma once
#include <initializer_list>
#include "answer_field_def.hpp"
#include "command_code.hpp"

namespace sonic_protocol_lib {

struct AnswerDef {
    CommandCode code;
    std::initializer_list<AnswerFieldDef> fields;
};

}