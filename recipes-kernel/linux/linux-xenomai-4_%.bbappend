#
# Copyright (c) Siemens AG, 2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend := "${THISDIR}/files:${THISDIR}/files/7.0.0/osadl:"
require osadl-patches.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://realtime.cfg"
SRC_URI:append:rpi4 = " file://rpi4-nopm.cfg"

SRC_URI += "${@'file://dbg.cfg' if d.getVar('XENOMAI_DEBUG') == '1' else ''}"

SRCREV = "e0f16425093bdecb38aa435434aa2149b1efe7a4"
