#
# Copyright (c) Siemens AG, 2026
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:prepend := "${THISDIR}/files:"
SRC_URI += "file://realtime.cfg"
SRC_URI:append:rpi4 = " file://rpi4-nopm.cfg"

SRC_URI += "${@'file://dbg.cfg' if d.getVar('XENOMAI_DEBUG') == '1' else ''}"

# v7.2-evl1-rebase tag, carries riscv support
GIT_BRANCH = "v7.2-evl-rebase"
GIT_BRANCH:riscv64 = "v7.2-evl-rebase"
SRCREV = "226f2e3ad97c7bc0347709bd94ac4f5990a6bd89"
