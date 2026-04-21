#
# Copyright (c) Siemens AG, 2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend := "${THISDIR}/files:${THISDIR}/files/7.0.0/osadl-evl:"
require osadl-patches.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://realtime.cfg"

SRC_URI += "${@'file://dbg.cfg' if d.getVar('XENOMAI_DEBUG') == '1' else ''}"

FILESEXTRAPATHS:prepend := "${THISDIR}/files/7.0.0/evl:"
