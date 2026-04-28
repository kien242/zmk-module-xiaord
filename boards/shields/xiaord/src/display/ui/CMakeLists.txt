# SPDX-License-Identifier: MIT

zephyr_library_sources(ui_btn.c)
zephyr_library_sources(home_buttons.c)

if(CONFIG_XIAORD_BG_USER_DEFINED)
  set(XIAORD_BG_USER_DEFINE_C "${CMAKE_CURRENT_SOURCE_DIR}/bg/bg_user_defined.c")
  set(XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE "${CONFIG_XIAORD_BG_USER_DEFINED_SOURCE_DIR}")

  if("${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}" STREQUAL "" AND NOT "$ENV{XIAORD_BG_USER_DEFINED_SOURCE_DIR}" STREQUAL "")
    set(XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE "$ENV{XIAORD_BG_USER_DEFINED_SOURCE_DIR}")
  endif()

  if("${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}" STREQUAL "" AND DEFINED ZMK_CONFIG)
    set(XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE "${ZMK_CONFIG}/xiaord-bg")
  endif()

  if(NOT "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}" STREQUAL "" AND
     NOT IS_ABSOLUTE "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}" AND
     DEFINED ZMK_CONFIG)
    set(XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE "${ZMK_CONFIG}/${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}")
  endif()

  if(NOT EXISTS "${XIAORD_BG_USER_DEFINE_C}" AND NOT "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}" STREQUAL "")
    file(TO_CMAKE_PATH "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}" XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED)
    message(STATUS "XIAORD_BG_USER_DEFINED: looking for background image in ${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}")

    if(EXISTS "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}")
      file(GLOB XIAORD_BG_USER_DEFINED_SOURCES LIST_DIRECTORIES false
        "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}/*.jpg"
        "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}/*.jpeg"
        "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}/*.png"
      )
      list(SORT XIAORD_BG_USER_DEFINED_SOURCES)
      list(LENGTH XIAORD_BG_USER_DEFINED_SOURCES XIAORD_BG_USER_DEFINED_SOURCE_COUNT)

      if(XIAORD_BG_USER_DEFINED_SOURCE_COUNT GREATER 0)
        list(GET XIAORD_BG_USER_DEFINED_SOURCES 0 XIAORD_BG_USER_DEFINED_SOURCE)
        message(STATUS "XIAORD_BG_USER_DEFINED: converting ${XIAORD_BG_USER_DEFINED_SOURCE}")
        find_package(Python3 COMPONENTS Interpreter QUIET)

        if(Python3_Interpreter_FOUND)
          get_filename_component(XIAORD_BG_USER_DEFINED_SOURCE_EXT "${XIAORD_BG_USER_DEFINED_SOURCE}" EXT)
          string(TOLOWER "${XIAORD_BG_USER_DEFINED_SOURCE_EXT}" XIAORD_BG_USER_DEFINED_SOURCE_EXT)

          if(NOT XIAORD_BG_USER_DEFINED_SOURCE_EXT STREQUAL ".png")
            execute_process(
              COMMAND "${Python3_EXECUTABLE}" -c "import PIL"
              RESULT_VARIABLE XIAORD_BG_USER_DEFINED_PIL_RESULT
              OUTPUT_QUIET
              ERROR_QUIET
            )
          else()
            set(XIAORD_BG_USER_DEFINED_PIL_RESULT 0)
          endif()

          if(NOT XIAORD_BG_USER_DEFINED_PIL_RESULT EQUAL 0 AND NOT XIAORD_BG_USER_DEFINED_SOURCE_EXT STREQUAL ".png")
            message(STATUS "XIAORD_BG_USER_DEFINED: Pillow not found; installing with pip")
            execute_process(
              COMMAND "${Python3_EXECUTABLE}" -m pip install --user pillow
              RESULT_VARIABLE XIAORD_BG_USER_DEFINED_PIP_RESULT
              OUTPUT_VARIABLE XIAORD_BG_USER_DEFINED_PIP_OUTPUT
              ERROR_VARIABLE XIAORD_BG_USER_DEFINED_PIP_ERROR
            )

            if(NOT XIAORD_BG_USER_DEFINED_PIP_RESULT EQUAL 0)
              message(WARNING "XIAORD_BG_USER_DEFINED: Pillow install failed; falling back to BG_1. ${XIAORD_BG_USER_DEFINED_PIP_ERROR}")
            endif()
          endif()

          execute_process(
            COMMAND
              "${Python3_EXECUTABLE}"
              "${CMAKE_CURRENT_SOURCE_DIR}/../../../tools/convert_xiaord_bg.py"
              "${XIAORD_BG_USER_DEFINED_SOURCE}"
              4
              --out-dir
              "${CMAKE_CURRENT_SOURCE_DIR}/bg"
            RESULT_VARIABLE XIAORD_BG_USER_DEFINED_CONVERT_RESULT
            OUTPUT_VARIABLE XIAORD_BG_USER_DEFINED_CONVERT_OUTPUT
            ERROR_VARIABLE XIAORD_BG_USER_DEFINED_CONVERT_ERROR
          )

          if(NOT XIAORD_BG_USER_DEFINED_CONVERT_RESULT EQUAL 0)
            message(WARNING "XIAORD_BG_USER_DEFINED conversion failed; falling back to BG_1. ${XIAORD_BG_USER_DEFINED_CONVERT_ERROR}")
          else()
            message(STATUS "XIAORD_BG_USER_DEFINED: generated ${XIAORD_BG_USER_DEFINE_C}")
          endif()
        else()
          message(WARNING "Python3 was not found; falling back to BG_1 for XIAORD_BG_USER_DEFINED.")
        endif()
      else()
        message(WARNING "No JPG/PNG files found in CONFIG_XIAORD_BG_USER_DEFINED_SOURCE_DIR; falling back to BG_1.")
      endif()
    else()
      message(WARNING "CONFIG_XIAORD_BG_USER_DEFINED_SOURCE_DIR does not exist; falling back to BG_1.")
    endif()
  endif()

  if(EXISTS "${XIAORD_BG_USER_DEFINE_C}")
    zephyr_library_sources(bg/bg_user_defined.c)
    zephyr_compile_definitions(XIAORD_LOCAL_BG_USER_DEFINED_AVAILABLE=1)
  else()
    zephyr_library_sources(bg/bg1.c)
  endif()
elseif(CONFIG_XIAORD_BG_1)
  zephyr_library_sources(bg/bg1.c)
elseif(CONFIG_XIAORD_BG_2)
  zephyr_library_sources(bg/bg2.c)
elseif(CONFIG_XIAORD_BG_3)
  zephyr_library_sources(bg/bg3.c)
endif()
