#pragma once

#include <cstdint>

namespace sonic_protocol_lib {

using CommandCode_t = int16_t;
using FieldName_t = int16_t;

inline static constexpr CommandCode_t COMMAND_CODE_E_COMMAND_INVALID {20000};
inline static constexpr FieldName_t FIELD_NAME_UNDEFINED {0};

}