#pragma once
#include <initializer_list>
#include "answer_field_def.hpp"
#include "command_code.hpp"
#include "etl/array.h"

namespace sonic_protocol_lib {

constexpr std::size_t MAX_ANSWER_FIELDS = 20;
struct AnswerDef {
    CommandCode code{CommandCode::INVALID};
    etl::array<AnswerFieldDef, MAX_ANSWER_FIELDS> fields;
};

}