#pragma once

#include <string_view>
#include <cassert>

namespace sonic_protocol_lib {


#define SI_UNIT_MEMBERS 
enum class SIUnit : char  {
    /**/SI_UNIT_MEMBERS/**/  // the python script will replace this
};
#undef SI_UNIT_MEMBERS 


#define SI_PREFIX_MEMBERS 
enum class SIPrefix : char {
    /**/SI_PREFIX_MEMBERS/**/  // the python script will replace this
};
#undef SI_PREFIX_MEMBERS 


#define SI_UNIT_TO_STR_CONVERSIONS assert(false);
inline std::string_view convert_si_unit_to_string(const SIUnit &value) {
    /**/SI_UNIT_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef SI_UNIT_TO_STR_CONVERSIONS 


#define SI_PREFIX_TO_STR_CONVERSIONS assert(false);
inline std::string_view convert_si_prefix_to_string(const SIPrefix &value) {
    /**/SI_PREFIX_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef SI_PREFIX_TO_STR_CONVERSIONS 

}