# SPDX-License-Identifier: MIT

zephyr_library_sources(ui_btn.c)
zephyr_library_sources(home_buttons.c)

if(CONFIG_XIAORD_BG_USER_DEFINED)
    set(XIAORD_BG_USER_DEFINED_C "${CMAKE_CURRENT_SOURCE_DIR}/bg/bg_user_defined.c")
    set(XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE "${CONFIG_XIAORD_BG_USER_DEFINED_SOURCE_DIR}")

    # --- Logic xác định thư mục nguồn ảnh ---
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

    # --- Bắt đầu quá trình xử lý ảnh ---
    if(NOT "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}" STREQUAL "")
        file(TO_CMAKE_PATH "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE}" XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED)

        if(EXISTS "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}")
            set(XIAORD_BG_USER_DEFINED_SOURCE "")
            foreach(ext png jpg jpeg PNG JPG JPEG)
                if(EXISTS "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}/bg_user_defined.${ext}")
                    set(XIAORD_BG_USER_DEFINED_SOURCE "${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}/bg_user_defined.${ext}")
                    break()
                endif()
            endforeach()

            if(NOT "${XIAORD_BG_USER_DEFINED_SOURCE}" STREQUAL "")
                message(STATUS "XIAORD_BG_USER_DEFINED: Found source ${XIAORD_BG_USER_DEFINED_SOURCE}")
                find_package(Python3 COMPONENTS Interpreter REQUIRED)

                # KIỂM TRA VÀ CÀI ĐẶT PILLOW TRỰC TIẾP TỪ CMAKE
                # Bước 1: Kiểm tra xem Pillow đã có chưa
                execute_process(
                    COMMAND "${Python3_EXECUTABLE}" -c "import PIL"
                    RESULT_VARIABLE PILLOW_CHECK_RES
                    OUTPUT_QUIET ERROR_QUIET
                )

                if(NOT PILLOW_CHECK_RES EQUAL 0)
                    message(STATUS "XIAORD_BG_USER_DEFINED: Pillow not found, attempting to install...")
                    
                    # Thử dùng ensurepip trước đề phòng môi trường không có pip
                    execute_process(COMMAND "${Python3_EXECUTABLE}" -m ensurepip --user OUTPUT_QUIET ERROR_QUIET)
                    
                    # Cài đặt Pillow với các cờ đặc biệt cho GitHub Actions (Ubuntu)
                    execute_process(
                        COMMAND "${Python3_EXECUTABLE}" -m pip install pillow --user --break-system-packages
                        RESULT_VARIABLE PILLOW_INSTALL_RES
                        ERROR_VARIABLE PILLOW_INSTALL_ERR
                    )
                    
                    if(NOT PILLOW_INSTALL_RES EQUAL 0)
                        message(WARNING "XIAORD_BG_USER_DEFINED: Pillow install failed: ${PILLOW_INSTALL_ERR}")
                    endif()
                endif()

                # CHẠY SCRIPT CHUYỂN ĐỔI
                execute_process(
                    COMMAND
                        "${Python3_EXECUTABLE}"
                        "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../../tools/convert_xiaord_bg.py"
                        "${XIAORD_BG_USER_DEFINED_SOURCE}"
                        "user_defined"
                        --out-dir "${CMAKE_CURRENT_SOURCE_DIR}/bg"
                    RESULT_VARIABLE XIAORD_BG_USER_DEFINED_CONVERT_RESULT
                    ERROR_VARIABLE XIAORD_BG_USER_DEFINED_CONVERT_ERROR
                    OUTPUT_VARIABLE XIAORD_BG_USER_DEFINED_CONVERT_OUT
                )

                if(NOT "${XIAORD_BG_USER_DEFINED_CONVERT_OUT}" STREQUAL "")
                    message(STATUS "${XIAORD_BG_USER_DEFINED_CONVERT_OUT}")
                endif()

                if(NOT XIAORD_BG_USER_DEFINED_CONVERT_RESULT EQUAL 0)
                    message(WARNING "XIAORD_BG_USER_DEFINED conversion failed: ${XIAORD_BG_USER_DEFINED_CONVERT_ERROR}")
                endif()
            else()
                message(WARNING "XIAORD_BG_USER_DEFINED: Could not find bg_user_defined.png/jpg in ${XIAORD_BG_USER_DEFINED_SOURCE_DIR_NORMALIZED}")
            endif()
        endif()
    endif()

    # --- Đăng ký source file vào Zephyr ---
    if(EXISTS "${XIAORD_BG_USER_DEFINED_C}")
        zephyr_library_sources(bg/bg_user_defined.c)
        zephyr_compile_definitions(XIAORD_LOCAL_BG_USER_DEFINED_AVAILABLE=1)
    else()
        message(STATUS "XIAORD_BG_USER_DEFINED: File .c not found, falling back to bg1.c")
        zephyr_library_sources(bg/bg1.c)
    endif()

elseif(CONFIG_XIAORD_BG_1)
    zephyr_library_sources(bg/bg1.c)
elseif(CONFIG_XIAORD_BG_2)
    zephyr_library_sources(bg/bg2.c)
elseif(CONFIG_XIAORD_BG_3)
    zephyr_library_sources(bg/bg3.c)
endif()