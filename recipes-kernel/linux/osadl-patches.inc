# OSADL add on patches for real-time kernel testing
#
# Copyright (c) Siemens AG, 2023-2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

SRC_URI += "file://add-nmi-callback-and-raw-parport-driver.patch \
            file://latency-histograms.patch \
            file://save-current-patchset-in-kernel.patch \
            file://sched-add-per-cpu-load-measurement.patch \
            file://osadl.cfg"
