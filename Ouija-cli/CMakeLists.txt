cmake_minimum_required(VERSION 3.10) # 3.1 << C_STANDARD 11

project(Ouija LANGUAGES C)

find_package(OpenCL REQUIRED)

# Add Windows icon resource for Ouija-CLI.exe
if (WIN32)
    set(OUIJA_ICON "${CMAKE_CURRENT_SOURCE_DIR}/icon.ouija.ico")
    set(OUIJA_RC_FILE "${CMAKE_CURRENT_SOURCE_DIR}/ouija.rc")
    if(NOT EXISTS ${OUIJA_RC_FILE})
        file(WRITE ${OUIJA_RC_FILE} "IDI_ICON1 ICON \"${OUIJA_ICON}\"\n")
    endif()
    set(OUIJA_CLI_SOURCES ouija.c ${OUIJA_RC_FILE})
else()
    set(OUIJA_CLI_SOURCES ouija.c)
endif()

add_executable(Ouija-CLI ${OUIJA_CLI_SOURCES})

target_link_libraries(Ouija-CLI PRIVATE OpenCL::OpenCL)

set_target_properties(Ouija-CLI PROPERTIES C_STANDARD 11
                                             C_STANDARD_REQUIRED ON
                                             C_EXTENSIONS ON)

# Update from OpenCL 1.0 to 2.0 to enable SVM features
target_compile_definitions(Ouija-CLI PRIVATE CL_TARGET_OPENCL_VERSION=200)

# Enable extreme optimizations for Release builds
if(MSVC)
    # Maximum optimization for speed with MSVC
    set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} /O2 /Ob3 /Oi /Ot /GL /Gy /DNDEBUG")
    # Enable profile-guided optimization flags
    set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} /fp:fast /arch:AVX2 /Qpar /Qpar-report:1")
    # Advanced MSVC optimizations
    set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} /Qvec-report:1 /GT /Gw")
    # Link-time optimizations
    set(CMAKE_EXE_LINKER_FLAGS_RELEASE "${CMAKE_EXE_LINKER_FLAGS_RELEASE} /OPT:REF /OPT:ICF /LTCG")
    # Debug builds should be debuggable, not optimized
    set(CMAKE_C_FLAGS_DEBUG "${CMAKE_C_FLAGS_DEBUG} /Od /Zi")
    set(CMAKE_EXE_LINKER_FLAGS_DEBUG "${CMAKE_EXE_LINKER_FLAGS_DEBUG} /DEBUG")
elseif(CMAKE_C_COMPILER_ID MATCHES "Clang" OR CMAKE_C_COMPILER_ID MATCHES "GNU")
    # Maximum optimization for GCC/Clang
    set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -O3 -DNDEBUG")
    # CPU-specific optimizations
    set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -march=native -mtune=native")
    # Fast math operations
    set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -ffast-math -funroll-loops -ftree-vectorize")
    # Link-time optimization
    set(CMAKE_C_FLAGS_RELEASE "${CMAKE_C_FLAGS_RELEASE} -flto")
    set(CMAKE_EXE_LINKER_FLAGS_RELEASE "${CMAKE_EXE_LINKER_FLAGS_RELEASE} -flto")
endif()

# Add include directories for vcpkg-installed libraries
# Check if CMAKE_TOOLCHAIN_FILE is defined before using it
if(DEFINED CMAKE_TOOLCHAIN_FILE)
    get_filename_component(TOOLCHAIN_DIR ${CMAKE_TOOLCHAIN_FILE} DIRECTORY)
    include_directories(${TOOLCHAIN_DIR}/../include)
else()
    message(WARNING "CMAKE_TOOLCHAIN_FILE is not defined. Assuming vcpkg include directory is reachable.")
    # You might need to manually specify the include path if the toolchain file isn't used
    # include_directories(path/to/vcpkg/installed/x64-windows/include)
endif()