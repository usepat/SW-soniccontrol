#pragma once

#include "sonic_protocol_lib/base/code.hpp"
#include <cstdint>
#include <etl/string_view.h>

#define PROTOCOL_NAMESPACE
namespace sonic_protocol_lib::/**/PROTOCOL_NAMESPACE/**/ {
#undef PROTOCOL_NAMESPACE


    
#define CODE_INJECTION 
    /**/CODE_INJECTION/**/  // the python script will replace this
#undef CODE_INJECTION 

}