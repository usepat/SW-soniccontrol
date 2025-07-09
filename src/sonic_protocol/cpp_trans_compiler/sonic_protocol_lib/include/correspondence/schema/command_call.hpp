#pragma once

#include <optional>
#include <cstdint>
#include "correspondence/schema/answer.hpp"
#include "correspondence/schema/internal_representation.hpp"
#include "error_handling/error_handler_interface.hpp"

namespace sonic_protocol_lib {

constexpr size_t NUM_MAX_COMMAND_ARGS = 4;
using IRObjectCommandCall = IRObject<NUM_MAX_COMMAND_ARGS>;

/**
 * @brief Abstract base structure for commands in a command pattern.
 * @ingroup Correspondence, Commands, Communication
 *
 * This structure is a key component of a command pattern that facilitates
 * internal software communication, independent of the underlying
 * communication/transmission protocol. The `Command_t` structure, along with
 * the `std::optional<BaseAnswer>` structure, forms the basis for executing commands within the
 * software. Each `Command_t` instance contains a `getCode` function to identify
 * its purpose, along with other members that hold specific values relevant to
 * the command. The `execute` method is designed to take a reference to a
 * `Model_t` object, which utilizes the appropriate driver to carry out the
 * command's intent using the provided values.
 */
class CommandCall {
private:
  CommandCode_t code;
  IRObjectCommandCall args;

public:
  CommandCall() = default;
  inline explicit CommandCall(const CommandCode_t code, const IRObjectCommandCall& args) : code{code}, args {args} {}

  /// Virtual destructor to ensure proper cleanup in derived classes.
  virtual ~CommandCall() = default;

  /**
   * @brief returns the code that is specific to the command struct
   *
   * @return CommandCode code enum
   */
  inline CommandCode_t getCode() const { return code; }

  inline IRObjectCommandCall getArgs() const { return args; }

  template<typename T>
  T get_arg_value(const FieldName_t& name) const {
      const IRField field {args.get_field(name)};
      return std::get<T>(field.value);
  }
};

}