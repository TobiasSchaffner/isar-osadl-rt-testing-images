#
# Copyright (c) Siemens AG, 2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit dpkg

DESCRIPTION = "IsolBench memory-interference microbenchmarks (latency probe)"
HOMEPAGE = "https://github.com/CSL-KU/IsolBench"
LICENSE = "MIT"

# IsolBench has no releases; pinned to the commit used for the paper.
SRC_URI = "git://github.com/CSL-KU/IsolBench.git;protocol=https;branch=master;destsuffix=isolbench-${PV} \
           file://debian"

SRCREV = "682680ebf7cdadaee7443ca9246dc424a05e60fa"

S = "${WORKDIR}/isolbench-${PV}"

DEBIAN_BUILD_DEPENDS = "debhelper (>= 10)"

TEMPLATE_FILES = "debian/control.tmpl"
TEMPLATE_VARS += "DEBIAN_BUILD_DEPENDS"

do_prepare_build[cleandirs] += "${S}/debian"
do_prepare_build() {
    cp -r ${WORKDIR}/debian ${S}
    deb_add_changelog
}
