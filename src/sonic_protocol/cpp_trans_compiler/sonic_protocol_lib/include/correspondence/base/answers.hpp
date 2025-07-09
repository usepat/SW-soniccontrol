#pragma once 

#include <cstdint>

#include "corrrespondence/schema/answer.hpp"
#include "sonic_protocol_lib/base/command_code.hpp"
#include "sonic_protocol_lib/base/field_names.hpp"
#include "sonic_protocol_lib/base/data_types.hpp"

namespace sonic_protocol_lib {

// Answer create_error(const CommandCode_t error_code, const etl::string_view& errorMsg) {
//     const auto field_name {sonic_protocol_lib::base::FieldName::ERROR_MESSAGE};
//     auto fields = { 
//         IRField{static_cast<FieldName_t>(field_name), errorMsg, BaseDataType::STRING} 
//     };
//     return Answer(error_code, IRObject(fields));
// }

}
