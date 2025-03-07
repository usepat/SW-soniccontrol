#pragma once
#include <cstdint>
#include <etl/string_view.h>

namespace sonic_protocol_lib {

using FieldName_t = int16_t;

#define FIELD_NAME_MEMBERS 

enum class FieldName : FieldName_t {
    /**/FIELD_NAME_MEMBERS/**/  // the python script will replace this
};

#define FIELD_NAME_TO_STR_CONVERSIONS assert(false);
inline etl::string_view convert_field_name_to_string(const FieldName &value) {
    /**/FIELD_NAME_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef FIELD_NAME_TO_STR_CONVERSIONS 

}