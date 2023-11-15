#
# Copyright (c) Siemens AG, 2023
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

require recipes-kernel/linux/linux-custom.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:${THISDIR}/files/6.6.0/:${THISDIR}/files/6.6.0/rt:${THISDIR}/files/6.6.0/osadl:"

SRC_URI += "git://github.com/raspberrypi/linux.git;protocol=https;branch=rpi-6.6.y;destsuffix=linux-rpi4-${PV}"

# Enable preempt_rt by applying rt patches and enabling the rt switches in the kernel config
SRC_URI += "file://patch-6.6-rt14.patch \
            file://preempt-rt.cfg"

SRCREV = "2020404c98525d7462578c8af7a2c204d3daf50a"

# Add the OSADL add on patches
SRC_URI += "file://add-nmi-callback-and-raw-parport-driver.patch \
            file://latency-histograms.patch \
            file://net-ipv4-icmp-ping-sysrq.patch \
            file://save-current-patchset-in-kernel.patch \
            file://sched-add-per-cpu-load-measurement.patch \
            file://osadl.cfg"

S = "${WORKDIR}/linux-rpi4-${PV}"

KERNEL_DEFCONFIG = "bcm2711_defconfig"

LINUX_VERSION_EXTENSION = "-isar"
