#
# Copyright (c) Siemens AG, 2023
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend := "${THISDIR}/files:${THISDIR}/files/5.15.0/:${THISDIR}/files/5.15.0/rt:${THISDIR}/files/5.15.0/osadl:"

# Enable preempt_rt by applying rt patches and enabling the rt switches in the kernel config
SRC_URI += "file://patch-5.15-rt17.patch \
            file://starfive_visionfive2_defconfig \
            file://preempt-rt.cfg"

# Enable preempt_rt with lazy support for riscv
SRC_URI += "file://asm-generic-preempt-also-check-preempt_lazy_count-fo.patch \
            file://riscv-add-lazy-preempt-support.patch \
            file://riscv-Allow-to-enable-RT.patch \
            file://fix-riscv64-CONFIG_PM-config-issues-VF2_v3.1.5.patch"

# Add the OSADL add on patches
SRC_URI += "file://add-nmi-callback-and-raw-parport-driver.patch \
            file://latency-histograms.patch \
            file://net-ipv4-icmp-ping-sysrq.patch \
            file://save-current-patchset-in-kernel.patch \
            file://sched-add-per-cpu-load-measurement.patch \
            file://osadl.cfg"

KERNEL_DEFCONFIG = "starfive_visionfive2_defconfig"

SRCREV = "4964ce0a869e92df26331833894c9d0fd84d80f3"
