#pragma once
#include <initializer_list>
#include "answer_field_def.hpp"
#include "command_code.hpp"
#include <span>

namespace sonic_protocol_lib {

struct AnswerDef {
    CommandCode code{CommandCode::E_INVALID_COMMAND};
    std::span<const AnswerFieldDef> fields;
};

}