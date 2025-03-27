add_library(sonic_protocol_lib INTERFACE)
set_target_properties(sonic_protocol_lib PROPERTIES LINKER_LANGUAGE CXX)
target_include_directories(sonic_protocol_lib INTERFACE "${CMAKE_CURRENT_SOURCE_DIR}/include")
target_link_libraries(sonic_protocol_lib INTERFACE etl::etl)
