#pragma once
#include <initializer_list>
#include "sonic_protocol_lib/base/answer_field_def.hpp"
#include "sonic_protocol_lib/base/code.hpp"
#include <span>

namespace sonic_protocol_lib {

struct AnswerDef {
    CommandCode_t code{COMMAND_CODE_E_COMMAND_INVALID};
    std::span<const AnswerFieldDef> fields;
};

}