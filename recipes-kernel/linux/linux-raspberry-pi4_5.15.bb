#
# Copyright (c) Siemens AG, 2023
#
# SPDX-License-Identifier: MIT

require recipes-kernel/linux/linux-custom.inc

SRC_URI += "git://github.com/raspberrypi/linux.git;protocol=https;branch=tobsch/rpi-5.15.y;destsuffix=linux-rpi4-${PV}"

# Enable preempt_rt by applying rt patches and enabling the rt switches in the kernel config
SRC_URI += "file://patch-5.15-rt17.patch \
            file://preempt-rt.cfg"

# Add the OSADL add on patches
SRC_URI += "file://add-nmi-callback-and-raw-parport-driver.patch \
            file://latency-histograms.patch \
            file://net-ipv4-icmp-ping-sysrq.patch \
            file://save-current-patchset-in-kernel.patch \
            file://sched-add-per-cpu-load-measurement.patch"

SRCREV = "14b35093ca68bf2c81bbc90aace5007142b40b40"

S = "${WORKDIR}/linux-rpi4-${PV}"

KERNEL_DEFCONFIG ?= "bcm2711_defconfig"

LINUX_VERSION_EXTENSION = "-isar"