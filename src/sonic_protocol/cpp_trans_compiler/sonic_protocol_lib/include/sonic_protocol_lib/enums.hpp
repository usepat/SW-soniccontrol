#pragma once

#include <string_view>
#include <cassert>
#include <optional>

namespace sonic_protocol_lib {


#define INPUT_SOURCE_MEMBERS 
enum class InputSource : char  {
    /**/INPUT_SOURCE_MEMBERS/**/  // the python script will replace this
};
#undef INPUT_SOURCE_MEMBERS 

#define COMMUNICATION_CHANNEL_MEMBERS
enum class CommunicationChannel : char {
    /**/COMMUNICATION_CHANNEL_MEMBERS/**/  // the python script will replace this
};
#undef COMMUNICATION_CHANNEL_MEMBERS

#define COMMUNICATION_PROTOCOL_MEMBERS
enum class CommunicationProtocol : char {
    /**/COMMUNICATION_PROTOCOL_MEMBERS/**/  // the python script will replace this
};
#undef COMMUNICATION_PROTOCOL_MEMBERS

#define DEVICE_TYPE_MEMBERS
enum class DeviceType : char {
    /**/DEVICE_TYPE_MEMBERS/**/  // the python script will replace this
};
#undef DEVICE_TYPE_MEMBERS

#define PROCEDURE_MEMBERS
enum class Procedure : char {
    /**/PROCEDURE_MEMBERS/**/  // the python script will replace this
};
#undef PROCEDURE_MEMBERS

#define STR_TO_INPUT_SOURCE_CONVERSIONS assert(false);
inline std::optional<InputSource> convert_string_to_input_source(const std::string_view &str) {
    /**/STR_TO_INPUT_SOURCE_CONVERSIONS/**/  // the python script will replace this
    return std::nullopt;
}
#undef STR_TO_INPUT_SOURCE_CONVERSIONS

#define STR_TO_COMMUNICATION_CHANNEL_CONVERSIONS assert(false);
inline  std::optional<CommunicationChannel> convert_string_to_communication_channel(const std::string_view &str) {
    /**/STR_TO_COMMUNICATION_CHANNEL_CONVERSIONS/**/  // the python script will replace this
    return std::nullopt;
}
#undef STR_TO_COMMUNICATION_CHANNEL_CONVERSIONS

#define STR_TO_COMMUNICATION_PROTOCOL_CONVERSIONS assert(false);
inline std::optional<CommunicationProtocol> convert_string_to_communication_protocol(const std::string_view &str) {
    /**/STR_TO_COMMUNICATION_PROTOCOL_CONVERSIONS/**/  // the python script will replace this
    return std::nullopt;
}
#undef STR_TO_COMMUNICATION_PROTOCOL_CONVERSIONS

#define STR_TO_WAVEFORM_CONVERSIONS assert(false);
inline std::optional<Waveform> convert_string_to_waveform(const std::string_view &str) {
    /**/STR_TO_WAVEFORM_CONVERSIONS/**/  // the python script will replace this
    return std::nullopt;
}
#undef STR_TO_WAVEFORM_CONVERSIONS



#define COMMUNICATION_CHANNEL_TO_STR_CONVERSIONS assert(false);
inline std::string_view convert_communication_channel_to_string(CommunicationChannel value) {
    /**/COMMUNICATION_CHANNEL_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef COMMUNICATION_CHANNEL_TO_STR_CONVERSIONS

#define COMMUNICATION_PROTOCOL_TO_STR_CONVERSIONS assert(false);
inline std::string_view convert_communication_protocol_to_string(CommunicationProtocol value) {
    /**/COMMUNICATION_PROTOCOL_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef COMMUNICATION_PROTOCOL_TO_STR_CONVERSIONS

#define DEVICE_TYPE_TO_STR_CONVERSIONS assert(false);
inline std::string_view convert_device_type_to_string(DeviceType value) {
    /**/DEVICE_TYPE_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef DEVICE_TYPE_TO_STR_CONVERSIONS

#define INPUT_SOURCE_TO_STR_CONVERSIONS assert(false);
inline std::string_view convert_input_source_to_string(InputSource value) {
    /**/INPUT_SOURCE_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef INPUT_SOURCE_TO_STR_CONVERSIONS

#define PROCEDURE_TO_STR_CONVERSIONS assert(false);
inline std::string_view convert_procedure_to_string(Procedure value) {
    /**/PROCEDURE_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef PROCEDURE_TO_STR_CONVERSIONS

#define WAVEFORM_TO_STR_CONVERSIONS assert(false);
inline std::string_view convert_waveform_to_string(Waveform value) {
    /**/WAVEFORM_TO_STR_CONVERSIONS/**/  // the python script will replace this
}
#undef WAVEFORM_TO_STR_CONVERSIONS

}