find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_RTI gnuradio-RTI)

FIND_PATH(
    GR_RTI_INCLUDE_DIRS
    NAMES gnuradio/RTI/api.h
    HINTS $ENV{RTI_DIR}/include
        ${PC_RTI_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_RTI_LIBRARIES
    NAMES gnuradio-RTI
    HINTS $ENV{RTI_DIR}/lib
        ${PC_RTI_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-RTITarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_RTI DEFAULT_MSG GR_RTI_LIBRARIES GR_RTI_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_RTI_LIBRARIES GR_RTI_INCLUDE_DIRS)
