#
# Copyright (c) Siemens AG, 2023-2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit linux-kernel

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "git://gitlab.com/Xenomai/xenomai4/linux-evl.git;protocol=https;branch=v7.2-evl-rebase;destsuffix=linux-preemptrt-${PV} \
            file://preempt-rt.cfg \
            file://realtime.cfg"
SRC_URI:append:rpi4 = " file://rpi4-nopm.cfg"

SRCREV = "226f2e3ad97c7bc0347709bd94ac4f5990a6bd89"

S = "${WORKDIR}/linux-preemptrt-${PV}"

LINUX_VERSION_EXTENSION = "-isar"
