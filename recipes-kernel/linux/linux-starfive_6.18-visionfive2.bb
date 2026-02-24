#
# Copyright (c) Siemens AG, 2023-2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit linux-kernel
require osadl-patches.inc

KERNEL_VERSION = "${PV}"

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "git://github.com/torvalds/linux.git;protocol=https;nobranch=1;destsuffix=linux-visionfive-${PV} \
            file://starfive_visionfive2_defconfig \
            file://preempt-rt.cfg"

SRCREV = "e9ec05addd1a067fc7cb218f20ecdc1b1b0898c0"

S = "${WORKDIR}/linux-visionfive-${PV}"

KERNEL_DEFCONFIG = "starfive_visionfive2_defconfig"

LINUX_VERSION_EXTENSION = "-isar"

COMPATIBLE_MACHINE = "starfive-visionfive2"
