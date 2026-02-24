#
# Copyright (c) Siemens AG, 2023-2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit linux-kernel
require osadl-patches.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "git://github.com/raspberrypi/linux.git;protocol=https;branch=rpi-${PV}.y;destsuffix=linux-rpi4-${PV} \
            file://bcm2711_defconfig \
            file://preempt-rt.cfg"

SRCREV = "${AUTOREV}"

S = "${WORKDIR}/linux-rpi4-${PV}"

KERNEL_DEFCONFIG = "bcm2711_defconfig"

LINUX_VERSION_EXTENSION = "-isar"
