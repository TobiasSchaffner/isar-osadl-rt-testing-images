#
# Copyright (c) Siemens AG, 2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT
FILESEXTRAPATHS:prepend := "${THISDIR}/files:${THISDIR}/files/6.18.0-evl/osadl:"
require osadl-patches.inc

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://0001-latmus-dump-histogram-data-on-ERESTARTSYS.patch"
