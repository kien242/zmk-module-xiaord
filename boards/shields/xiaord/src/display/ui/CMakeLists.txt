# SPDX-License-Identifier: MIT

zephyr_library_sources(ui_btn.c)
zephyr_library_sources(home_buttons.c)

if(CONFIG_XIAORD_BG_USER_DEFINED)
    set(XIAORD_BG_USER_DEFINED_C "${CMAKE_CURRENT_SOURCE_DIR}/bg/bg_user_defined.c")
    set(XIAORD_BG_USER_DEFINED_SOURCE_DIR_EFFECTIVE "${CONFIG_XIAORD_BG_USER_DEFINED_SOURCE_DIR}")

    # --- Logic xác định thư mục nguồn (Giữ nguyên của bạn) ---
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
    
    # 1. Lấy đuôi file
    get_filename_component(SOURCE_EXT "${XIAORD_BG_USER_DEFINED_SOURCE}" EXT)
    string(TOLOWER "${SOURCE_EXT}" SOURCE_EXT)

    # 2. Kiểm tra Pillow (Chỉ khi cần - không phải PNG hoặc muốn chắc chắn)
    set(NEED_INSTALL_PILLOW FALSE)
    if(NOT SOURCE_EXT STREQUAL ".png")
        execute_process(COMMAND "${Python3_EXECUTABLE}" -c "import PIL" RESULT_VARIABLE PIL_FOUND OUTPUT_QUIET ERROR_QUIET)
        if(NOT PIL_FOUND EQUAL 0)
            set(NEED_INSTALL_PILLOW TRUE)
        endif()
    endif()

    # 3. Kiểm tra PIP trước khi cài
    if(NEED_INSTALL_PILLOW)
        execute_process(COMMAND "${Python3_EXECUTABLE}" -m pip --version RESULT_VARIABLE PIP_FOUND OUTPUT_QUIET ERROR_QUIET)
        if(PIP_FOUND EQUAL 0)
            message(STATUS "Installing Pillow via pip...")
            execute_process(COMMAND "${Python3_EXECUTABLE}" -m pip install pillow --user --break-system-packages)
        else()
            message(WARNING "Pip not found. Cannot install Pillow. Conversion might fail.")
        endif()
    endif()

    # 4. Chạy script chuyển đổi (Bọc trong logic an toàn)
    execute_process(
        COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../../../../../../tools/convert_xiaord_bg.py"
                "${XIAORD_BG_USER_DEFINED_SOURCE}" "bg_user_defined" --out-dir "${CMAKE_CURRENT_SOURCE_DIR}/bg"
        RESULT_VARIABLE CONVERT_RES
        ERROR_VARIABLE CONVERT_ERR
        OUTPUT_VARIABLE CONVERT_OUT
    )

                # Hiển thị log từ Python (bao gồm cả dòng "Successfully generated" màu xanh của bạn)
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
