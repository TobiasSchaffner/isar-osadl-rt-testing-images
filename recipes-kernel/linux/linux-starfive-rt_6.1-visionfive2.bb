#
# Copyright (c) Siemens AG, 2023
#
# SPDX-License-Identifier: MIT

require recipes-kernel/linux/linux-custom.inc

SRC_URI += " \
    git://github.com/TobiasSchaffner/linux.git;protocol=https;branch=tobsch/JH7110_VisionFive2_preempt_rt;destsuffix=linux-visionfive-${PV} \
    file://starfive_visionfive2_defconfig \
    file://starfive2_extra.cfg \
    file://preempt-rt.cfg"

SRCREV = "dfa52cc14f3b4a4a9a4827aa7cbd12830832d68c"

S = "${WORKDIR}/linux-visionfive-${PV}"

KERNEL_DEFCONFIG = "starfive_visionfive2_defconfig"

LINUX_VERSION_EXTENSION = "-isar"
