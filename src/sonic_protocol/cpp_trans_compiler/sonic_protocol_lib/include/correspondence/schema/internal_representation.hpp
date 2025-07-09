#pragma once

#include <array>
#include <optional>
#include <etl/string_view.h>
#include <etl/vector.h>
#include <variant>
#include <functional> // for reference_wrapper

#include "sonic_protocol_lib/schema/code.hpp"
#include "sonic_protocol_lib/schema/field_type_def.hpp"
#include "sonic_protocol_lib/schema/protocol_def.hpp"


namespace sonic_protocol_lib {

constexpr size_t MAX_STR_LEN = 50;


size_t constexpr MAX_MESSAGE_STRING_LEN = 4096;
using MessageString = etl::string<MAX_MESSAGE_STRING_LEN>;

using MessageStringRef = std::reference_wrapper<const MessageString>;

struct IREnum {
    const EnumValue_t enum_member;
};

using IRValue = std::variant<
        uint8_t, uint16_t, uint32_t, float, bool, etl::string_view, IREnum,
        Version, MessageStringRef>; // TODO: add DateTime, delete MessageStringRef

struct IRField {
    const FieldName_t name;
    const IRValue value;
    const DataType_t type;

    inline bool check_type(const DataType_t& type) const {
        return this->type == type;
    }
};

template<size_t N>
using IRFieldsVec = etl::vector<IRField, N>;

template<size_t N = 16>
class IRObject {
private:
    IRFieldsVec<N> fields;

public: 
    IRObject(const decltype(fields)& fields) : fields {fields} {}

    template <typename FieldNameEnum>
    IRField get_field(const FieldNameEnum& name) const {
        for (const auto& field : fields) {
            if (field.name == static_cast<FieldName_t>(name)) {
                return field;
            }
        }
        customAssert(false, std::format("Field not found: %s", convert_field_name_to_string(name).data()));
        assert(false);  //  We need this here because else we have no return statement
    }
};

}