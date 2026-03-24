#
# Copyright (c) Siemens AG, 2023-2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit linux-kernel
require osadl-patches.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:${THISDIR}/files/7.0.0/osadl-preemptrt:"
require osadl-patches.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "git://github.com/raspberrypi/linux.git;protocol=https;branch=rpi-${PV}.y;destsuffix=linux-rpi4-${PV} \
            file://preempt-rt.cfg \
            file://realtime.cfg"

SRCREV = "${AUTOREV}"

S = "${WORKDIR}/linux-rpi4-${PV}"

LINUX_VERSION_EXTENSION = "-isar"
