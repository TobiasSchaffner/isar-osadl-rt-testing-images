#
# Copyright (c) Siemens AG, 2023
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

FILESEXTRAPATHS:append := "${THISDIR}/files:"

SRC_URI += "file://cmdline.txt.tmpl"

TEMPLATE_VARS = "MACHINE_SERIAL BAUDRATE_TTY IMAGE_KERNEL_CMDLINE_TUNE"
TEMPLATE_FILES = "cmdline.txt.tmpl"

