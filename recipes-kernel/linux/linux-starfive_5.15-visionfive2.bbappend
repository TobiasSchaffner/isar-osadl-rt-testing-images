#
# Copyright (c) Siemens AG, 2023
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"

# Enable preempt_rt by applying rt patches and enabling the rt switches in the kernel config
SRC_URI += "file://patch-5.15-rt17.patch \
            file://preempt-rt.cfg"

# Enable preempt_rt with lazy support for riscv
SRC_URI += "file://asm-generic-preempt-also-check-preempt_lazy_count-fo.patch \
            file://riscv-add-lazy-preempt-support.patch \
            file://riscv-Allow-to-enable-RT.patch \
            file://fix-riscv64-CPNFIG_PM-config-issues-VF2_v2.11.5.patch"

# Add the OSADL add on patches
SRC_URI += "file://add-nmi-callback-and-raw-parport-driver.patch \
            file://latency-histograms.patch \
            file://net-ipv4-icmp-ping-sysrq.patch \
            file://save-current-patchset-in-kernel.patch \
            file://sched-add-per-cpu-load-measurement.patch"
