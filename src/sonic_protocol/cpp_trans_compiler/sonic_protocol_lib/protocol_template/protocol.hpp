#pragma once

#include <array>
#include <cstdint>
#include <string_view>
#include <span>
#include <optional>

#include "sonic_protocol_lib/schema/answer_def.hpp"
#include "sonic_protocol_lib/schema/code.hpp"
#include "sonic_protocol_lib/schema/command_def.hpp"

#include "sonic_protocol_lib//**/PROTOCOL_NAMESPACE/**//command_code.hpp"
#include "sonic_protocol_lib//**/PROTOCOL_NAMESPACE/**//consts.hpp"
#include "sonic_protocol_lib//**/PROTOCOL_NAMESPACE/**//data_types.hpp"
#include "sonic_protocol_lib//**/PROTOCOL_NAMESPACE/**//field_names.hpp"

#define PROTOCOL_NAMESPACE

namespace sonic_protocol_lib::enum_str_conversions {
    using namespace ::/**/PROTOCOL_NAMESPACE/**/::enum_str_conversions;
}

namespace sonic_protocol_lib::/**/PROTOCOL_NAMESPACE/**/ {

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

#define PROTOCOL_CLASS
/**/PROTOCOL_CLASS/**/ // the python script will replace this
#undef PROTOCOL_CLASS

}

#undef PROTOCOL_NAMESPACE
