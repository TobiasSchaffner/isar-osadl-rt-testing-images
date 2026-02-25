#
# Copyright (c) Siemens AG, 2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit dpkg-raw

DESCRIPTION = "cyclictest-compatible wrapper using latmus (EVL/Xenomai 4)"

SRC_URI = "file://cyclictest-latmus"

DEBIAN_DEPENDS = "python3, libevl"

do_install() {
    install -v -d ${D}/usr/bin
    install -v -m 755 ${WORKDIR}/cyclictest-latmus ${D}/usr/bin/cyclictest
}
