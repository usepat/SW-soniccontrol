#pragma once
#include <cstdint>

namespace sonic_protocol_lib {

using FieldName_t = int16_t;

#define FIELD_NAME_MEMBERS 

enum class FieldName : FieldName_t {
    /**/FIELD_NAME_MEMBERS/**/  // the python script will replace this
};

}