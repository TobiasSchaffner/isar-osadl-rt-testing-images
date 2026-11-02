#
# Copyright (c) Siemens AG, 2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit dpkg

DESCRIPTION = "Memory-contention experiments and tools for the JH7110 (SiFive U74-MC)"
LICENSE = "MIT"

# The sources are kept in this layer, so the layer commit pins them.
SRC_URI = "file://src file://debian"

S = "${WORKDIR}/${PN}-${PV}"

DEBIAN_BUILD_DEPENDS = "debhelper (>= 10)"

TEMPLATE_FILES = "debian/control.tmpl"
TEMPLATE_VARS += "DEBIAN_BUILD_DEPENDS"

do_prepare_build[cleandirs] += "${S}"
do_prepare_build() {
    cp -r ${WORKDIR}/src/. ${S}
    cp -r ${WORKDIR}/debian ${S}
    deb_add_changelog
}
