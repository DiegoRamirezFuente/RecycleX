find_package(Python3 REQUIRED)

add_custom_target(run_python_script
    COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/src/my_rtde_script.py
    WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}/src
    COMMENT "Ejecutando script de Python desde CMake"
)
