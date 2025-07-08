#pragma once
#include <initializer_list>
#include "sonic_protocol_lib/schema/answer_field_def.hpp"
#include "sonic_protocol_lib/schema/code.hpp"
#include <span>

namespace sonic_protocol_lib {

struct AnswerDef {
    CommandCode_t code{0};
    std::span<const AnswerFieldDef> fields;
};

}