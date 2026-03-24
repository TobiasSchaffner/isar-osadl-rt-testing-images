#
# Copyright (c) Siemens AG, 2023-2025
#
# SPDX-License-Identifier: MIT

inherit opensbi

DESCRIPTION = "OpenSBI firmware for StarFive VisionFive 2"

SRC_URI += "https://github.com/riscv-software-src/opensbi/archive/refs/tags/v${PV}.tar.gz;downloadfilename=opensbi-${PV}.tar.gz"
SRC_URI[sha256sum] = "fb1ae61a85e966322101acb1c982f84d9eaafc4de7dd474a7d7546d9bb321c6f"

S = "${WORKDIR}/opensbi-${PV}"

OPENSBI_EXTRA_BUILDARGS = "FW_TEXT_START=0x40000000 FW_OPTIONS=0"
OPENSBI_BIN = "fw_dynamic.bin"

COMPATIBLE_MACHINE = "^(starfive-visionfive2)$"
