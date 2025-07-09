#pragma once 


#include <cstdint>
#include <etl/string_view.h>

#include "corrrespondence/schema/answer.hpp"
#include "sonic_protocol_lib//**/PROTOCOL_NAMESPACE/**//command_code.hpp"
#include "sonic_protocol_lib//**/PROTOCOL_NAMESPACE/**//field_names.hpp"
#include "sonic_protocol_lib//**/PROTOCOL_NAMESPACE/**//data_types.hpp"

#define PROTOCOL_NAMESPACE
namespace sonic_protocol_lib::/**/PROTOCOL_NAMESPACE/**/::answers {
#undef PROTOCOL_NAMESPACE

#define ANSWERS 
/**/ANSWERS/**/  // the python script will replace this
#undef ANSWERS 

}