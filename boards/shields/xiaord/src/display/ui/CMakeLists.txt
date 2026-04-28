# SPDX-License-Identifier: MIT

zephyr_library_sources(ui_btn.c)
zephyr_library_sources(home_buttons.c)

if(CONFIG_XIAORD_BG_USER_DEFINED)
  set(XIAORD_BG_USER_C "${CMAKE_CURRENT_SOURCE_DIR}/bg/bg_user_defined.c")
  set(XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE "${CONFIG_XIAORD_BG_USER_DEFINED_SOURCE_DIR}")

  if("${XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE}" STREQUAL "" AND NOT "$ENV{XIAORD_BG_USER_DEFINED_SOURCE_DIR}" STREQUAL "")
    set(XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE "$ENV{XIAORD_BG_USER_DEFINED_SOURCE_DIR}")
  endif()

  if("${XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE}" STREQUAL "" AND DEFINED ZMK_CONFIG)
    set(XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE "${ZMK_CONFIG}/xiaord-bg")
  endif()

  if(NOT "${XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE}" STREQUAL "" AND
     NOT IS_ABSOLUTE "${XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE}" AND
     DEFINED ZMK_CONFIG)
    set(XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE "${ZMK_CONFIG}/${XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE}")
  endif()

  if(NOT "${XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE}" STREQUAL "")
    file(TO_CMAKE_PATH "${XIAORD_BG_USER_SOURCE_DIR_EFFECTIVE}" XIAORD_BG_USER_SOURCE_DIR_NORMALIZED)
    message(STATUS "XIAORD_BG_USER: looking for background image in ${XIAORD_BG_USER_SOURCE_DIR_NORMALIZED}")

    if(EXISTS "${XIAORD_BG_USER_SOURCE_DIR_NORMALIZED}")
      file(GLOB XIAORD_BG_USER_SOURCES LIST_DIRECTORIES false
        "${XIAORD_BG_USER_SOURCE_DIR_NORMALIZED}/bg_user_defined.jpg"
        "${XIAORD_BG_USER_SOURCE_DIR_NORMALIZED}/bg_user_defined.jpeg"
        "${XIAORD_BG_USER_SOURCE_DIR_NORMALIZED}/bg_user_defined.png"
      )
      list(SORT XIAORD_BG_USER_SOURCES)
      list(LENGTH XIAORD_BG_USER_SOURCES XIAORD_BG_USER_SOURCE_COUNT)

      if(XIAORD_BG_USER_SOURCE_COUNT GREATER 0)
        list(GET XIAORD_BG_USER_SOURCES 0 XIAORD_BG_USER_SOURCE)
        message(STATUS "XIAORD_BG_USER: converting ${XIAORD_BG_USER_SOURCE}")
        find_package(Python3 COMPONENTS Interpreter QUIET)

        if(Python3_Interpreter_FOUND)
          # Kiểm tra Pillow (giữ nguyên logic gốc của bạn)
          get_filename_component(XIAORD_BG_USER_SOURCE_EXT "${XIAORD_BG_USER_SOURCE}" EXT)
          string(TOLOWER "${XIAORD_BG_USER_SOURCE_EXT}" XIAORD_BG_USER_SOURCE_EXT)

          if(NOT XIAORD_BG_USER_SOURCE_EXT STREQUAL ".png")
            execute_process(
              COMMAND "${Python3_EXECUTABLE}" -c "import PIL"
              RESULT_VARIABLE XIAORD_BG_USER_PIL_RESULT
              OUTPUT_QUIET
              ERROR_QUIET
            )
          else()
            set(XIAORD_BG_USER_PIL_RESULT 0)
          endif()

          if(NOT XIAORD_BG_USER_PIL_RESULT EQUAL 0 AND NOT XIAORD_BG_USER_SOURCE_EXT STREQUAL ".png")
            message(STATUS "XIAORD_BG_USER: Pillow not found; installing with pip")
            execute_process(
              COMMAND "${Python3_EXECUTABLE}" -m pip install --user pillow
              RESULT_VARIABLE XIAORD_BG_USER_PIP_RESULT
              OUTPUT_VARIABLE XIAORD_BG_USER_PIP_OUTPUT
              ERROR_VARIABLE XIAORD_BG_USER_PIP_ERROR
            )
          endif()

          execute_process(
            COMMAND
              "${Python3_EXECUTABLE}"
              "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../../tools/convert_xiaord_bg.py"
              "${XIAORD_BG_USER_SOURCE}"
              "user_defined"
              --out-dir
              "${CMAKE_CURRENT_SOURCE_DIR}/bg"
            RESULT_VARIABLE XIAORD_BG_USER_CONVERT_RESULT
            OUTPUT_VARIABLE XIAORD_BG_USER_CONVERT_OUTPUT
            ERROR_VARIABLE XIAORD_BG_USER_CONVERT_ERROR
          )

          if(NOT XIAORD_BG_USER_CONVERT_RESULT EQUAL 0)
            message(WARNING "XIAORD_BG_USER conversion failed; falling back to BG_1. ${XIAORD_BG_USER_CONVERT_ERROR}")
          else()
            message(STATUS "XIAORD_BG_USER: generated ${XIAORD_BG_USER_C}")
          endif()
        else()
          message(WARNING "Python3 was not found; falling back to BG_1 for XIAORD_BG_USER.")
        endif()
      else()
        message(WARNING "No bg_user_defined.png/jpg found; falling back to BG_1.")
      endif()
    else()
      message(WARNING "Source directory does not exist; falling back to BG_1.")
    endif()
  endif()

  if(EXISTS "${XIAORD_BG_USER_C}")
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