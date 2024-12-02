#pragma once
#include <initializer_list>
#include "answer_field_def.hpp"
#include "command_code.hpp"
#include <span>

namespace sonic_protocol_lib {

struct AnswerDef {
    CommandCode code{CommandCode::INVALID};
    std::span<const AnswerFieldDef> fields;
};

}