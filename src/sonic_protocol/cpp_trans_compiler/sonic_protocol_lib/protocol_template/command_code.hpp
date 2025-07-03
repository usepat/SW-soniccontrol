#pragma once

#include <cstdint>
#include <etl/string_view.h>
#include "sonic_protocol_lib/base/code.hpp"

#define PROTOCOL_NAMESPACE
namespace sonic_protocol_lib::/**/PROTOCOL_NAMESPACE/**/ {
#undef PROTOCOL_NAMESPACE

#define COMMAND_CODE 
/**/COMMAND_CODE/**/  // the python script will replace this
#undef COMMAND_CODE 

#define IS_VALID_CODE 
/**/IS_VALID_CODE/**/  // the python script will replace this
#undef IS_VALID_CODE 

}
