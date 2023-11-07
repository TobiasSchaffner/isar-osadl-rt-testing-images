#
# Copyright (c) Siemens AG, 2023
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

require recipes-kernel/linux/linux-custom.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:${THISDIR}/files/6.6.0/:${THISDIR}/files/6.6.0/rt:${THISDIR}/files/6.6.0/osadl:"

# Enable preempt_rt by applying rt patches and enabling the rt switches in the kernel config
SRC_URI += "git://github.com/torvalds/linux.git;protocol=https;branch=master;destsuffix=linux-visionfive-${PV} \
            file://patch-6.6-rc6-rt10.patch \
            file://bcm2711_defconfig \
            file://preempt-rt.cfg"

SRCREV = "58720809f52779dc0f08e53e54b014209d13eebb"

# Add the OSADL add on patches
SRC_URI += "file://add-nmi-callback-and-raw-parport-driver.patch \
            file://latency-histograms.patch \
            file://net-ipv4-icmp-ping-sysrq.patch \
            file://save-current-patchset-in-kernel.patch \
            file://sched-add-per-cpu-load-measurement.patch \
            file://osadl.cfg"

S = "${WORKDIR}/linux-visionfive-${PV}"

KERNEL_DEFCONFIG = "bcm2711_defconfig"

LINUX_VERSION_EXTENSION = "-isar"
