#
# Copyright (c) Siemens AG, 2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit dpkg

DESCRIPTION = "BYTE Unix benchmark suite"
HOMEPAGE = "https://github.com/kdlucas/byte-unixbench"
LICENSE = "GPL-2.0"

SRC_URI = "git://github.com/kdlucas/byte-unixbench.git;protocol=https;branch=master;destsuffix=unix-bench-${PV} \
           file://debian"

SRCREV = "986b674a1e50eedd944bc08d6bdc8be925b2bc65"

S = "${WORKDIR}/unix-bench-${PV}"

DEBIAN_BUILD_DEPENDS = "debhelper (>= 10)"

TEMPLATE_FILES = "debian/control.tmpl"
TEMPLATE_VARS += "DEBIAN_BUILD_DEPENDS"

do_prepare_build[cleandirs] += "${S}/debian"
do_prepare_build() {
    cp -r ${WORKDIR}/debian ${S}
    deb_add_changelog
}
