#pragma once
#include <cstdint>
#include <etl/string_view.h>

namespace sonic_protocol_lib {


    
using FieldName_t = int16_t;

#define FIELD_NAME_MEMBERS 

#define FIELD_NAME_NAME

enum class /**/FIELD_NAME_NAME/**/ : FieldName_t {
    /**/FIELD_NAME_MEMBERS/**/  // the python script will replace this
};
namespace {
using EFieldName = /**/FIELD_NAME_NAME/**/;
}

#define FIELD_NAME_TO_STR_CONVERSIONS assert(false);
inline etl::string_view convert_field_name_to_string(const /**/FIELD_NAME_NAME/**/ &value) {
    /**/FIELD_NAME_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef FIELD_NAME_TO_STR_CONVERSIONS 

}