#pragma once

#include <cstdint>
#include <etl/string_view.h>

#define PROTOCOL_NAMESPACE
namespace sonic_protocol_lib::/**/PROTOCOL_NAMESPACE/**/::consts {
#undef PROTOCOL_NAMESPACE

#define CONSTS 
/**/CONSTS/**/  // the python script will replace this
#undef CONSTS 

}