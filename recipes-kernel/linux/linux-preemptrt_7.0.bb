#
# Copyright (c) Siemens AG, 2023-2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit linux-kernel

FILESEXTRAPATHS:prepend := "${THISDIR}/files:${THISDIR}/files/7.0.0/osadl:"
require osadl-patches.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

SRC_URI += "git://gitlab.com/Xenomai/xenomai4/linux-evl.git;protocol=https;branch=wip/evl-riscv;destsuffix=linux-preemptrt-${PV} \
            file://preempt-rt.cfg \
            file://realtime.cfg"
SRC_URI:append:rpi4 = " file://rpi4-nopm.cfg"

SRCREV = "e0f16425093bdecb38aa435434aa2149b1efe7a4"

S = "${WORKDIR}/linux-preemptrt-${PV}"

LINUX_VERSION_EXTENSION = "-isar"
