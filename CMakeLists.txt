cmake_minimum_required(VERSION 3.14)
project(apriltag)

find_package(Threads REQUIRED)
find_package(OpenCV QUIET)

include_directories(.)
aux_source_directory(common COMMON_SRC)
set(APRILTAG_SRCS apriltag.c apriltag_pose.c apriltag_quad_thresh.c)

set(CMAKE_BUILD_TYPE Release)

# Library
file(GLOB TAG_FILES ${CMAKE_SOURCE_DIR}/tag*.c)
set_source_files_properties(SOURCE ${TAG_FILES} PROPERTIES COMPILE_FLAGS -O0)
add_library(${PROJECT_NAME} STATIC ${APRILTAG_SRCS} ${COMMON_SRC} ${TAG_FILES})
set_target_properties(${PROJECT_NAME} PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_link_libraries(${PROJECT_NAME} Threads::Threads)
if (MSVC)
    # winmm is necessary for __imp_timeGetTime
    target_link_libraries(${PROJECT_NAME} winmm)
else()
    target_link_libraries(${PROJECT_NAME} m)
endif()

set_target_properties(${PROJECT_NAME} PROPERTIES SOVERSION 3 VERSION 3.1.0)

include(GNUInstallDirs)
target_include_directories(${PROJECT_NAME} PUBLIC
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/>"
    "$<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/common>"
    "$<INSTALL_INTERFACE:$<INSTALL_PREFIX>/${CMAKE_INSTALL_INCLUDEDIR}>/apriltag")

set_target_properties(${PROJECT_NAME} PROPERTIES
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_INSTALL_LIBDIR}
    LIBRARY_OUTPUT_DIRECTORY ${CMAKE_INSTALL_LIBDIR}
)


# install library
install(TARGETS ${PROJECT_NAME} EXPORT apriltag
    LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
    ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
)

# install header file hierarchy
file(GLOB_RECURSE HEADER_FILES RELATIVE ${CMAKE_SOURCE_DIR} *.h)
foreach(HEADER ${HEADER_FILES})
    string(REGEX MATCH "(.*)[/\\]" DIR ${HEADER})
    install(FILES ${HEADER} DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/${PROJECT_NAME}/${DIR})
endforeach()

# export library
install(EXPORT apriltag
    DESTINATION share/apriltag/cmake
    FILE apriltagConfig.cmake
)

FILE(READ apriltag.pc.in PKGC)
STRING(REGEX REPLACE "^prefix=" "prefix=${CMAKE_INSTALL_PREFIX}" PKGC_CONF "${PKGC}" )
FILE(WRITE ${PROJECT_BINARY_DIR}/apriltag.pc ${PKGC_CONF})
install(FILES "${PROJECT_BINARY_DIR}/apriltag.pc" DESTINATION "lib/pkgconfig/")

# Python wrapper

set(Python3_FIND_REGISTRY "LAST" CACHE STRING "")
find_package(Python3 COMPONENTS Interpreter Development NumPy)

foreach(X detect py_type)
add_custom_command(
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/apriltag_${X}.docstring.h
    COMMAND < ${CMAKE_SOURCE_DIR}/apriltag_${X}.docstring ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/python_to_string.py > apriltag_${X}.docstring.h
    #WORKING_DIRECTORY ${PROJECT_BINARY_DIR}
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    DEPENDS apriltag_${X}.docstring
    )
endforeach()

# find venv first
Python3_add_library(pyapriltag MODULE
    apriltag_pywrap.c
    apriltag_detect.docstring.h
    apriltag_py_type.docstring.h
    )
target_link_libraries(pyapriltag PRIVATE Python3::NumPy ${PROJECT_NAME})
target_include_directories(pyapriltag
    PRIVATE ${CMAKE_CURRENT_BINARY_DIR}
)
set_target_properties(pyapriltag PROPERTIES OUTPUT_NAME "apriltag")

install(
    TARGETS pyapriltag
    DESTINATION ${Python3_SITEARCH}
    COMPONENT python
)

add_custom_target(pyinstall
    DEPENDS pyapriltag
    COMMAND "${CMAKE_COMMAND}" -DCMAKE_INSTALL_COMPONENT=python -P "${CMAKE_BINARY_DIR}/cmake_install.cmake"
)

#execute_process(COMMAND python3 -m site --user-site OUTPUT_VARIABLE PY_DEST)
#string(STRIP ${PY_DEST} PY_DEST)
#install(CODE "execute_process(COMMAND cp ${PROJECT_BINARY_DIR}/apriltag${PY_EXT_SUFFIX} ${PY_DEST})")


# Examples
# apriltag_demo
add_executable(apriltag_demo example/apriltag_demo.c)
target_link_libraries(apriltag_demo apriltag)

# opencv_demo
if(OpenCV_FOUND)
    add_executable(opencv_demo example/opencv_demo.cc)
    target_link_libraries(opencv_demo apriltag ${OpenCV_LIBRARIES})
    install(TARGETS opencv_demo RUNTIME DESTINATION bin)
endif(OpenCV_FOUND)

# install example programs
install(TARGETS apriltag_demo RUNTIME DESTINATION bin)

