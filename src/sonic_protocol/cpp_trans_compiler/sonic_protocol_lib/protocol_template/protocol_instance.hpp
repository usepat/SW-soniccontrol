#pragma once
#include <initializer_list>
#include <array>
#include <cstdint>

#include "sonic_protocol_lib/base/protocol.hpp"
#include "etl/array.h"

namespace sonic_protocol_lib {

// begin anonymous namespace
// this namespace hides the elements. so that they are only accessible in this translation unit
namespace {

#define ALLOWED_VALUES
/**/ALLOWED_VALUES/**/ // the python script will replace this
#undef ALLOWED_VALUES

#define FIELD_LIMITS
/**/FIELD_LIMITS/**/ // the python script will replace this
#undef FIELD_LIMITS

#define FIELD_DEFS
/**/FIELD_DEFS/**/ // the python script will replace this
#undef FIELD_DEFS

#define PARAM_DEFS
/**/PARAM_DEFS/**/ // the python script will replace this
#undef PARAM_DEFS

#define COMMAND_DEFS
inline constexpr std::array<ParamDef, 0> EMPTY_PARAMS{};
/**/COMMAND_DEFS/**/ // the python script will replace this
#undef COMMAND_DEFS

#define ANSWER_DEFS
/**/ANSWER_DEFS/**/ // the python script will replace this
#undef ANSWER_DEFS

} // end anonymous namespace

#define PROTOCOL_INSTANCE_NAME

#define PROTOCOL
constexpr Protocol /**/PROTOCOL_INSTANCE_NAME/**/ = /**/PROTOCOL_INSTANCE/**/; // the python script will replace this
#undef PROTOCOL

}