#
# Copyright (c) Siemens AG, 2023
#
# SPDX-License-Identifier: MIT

require recipes-kernel/linux/linux-custom.inc

DEB_BUILD_PROFILES = ""

def get_patches(d, patchdir):
    import glob

    files_dir = os.path.join(d.getVar('THISDIR'), 'files')
    patch_glob = os.path.join(files_dir, patchdir, '*.patch')
    patches = glob.glob(patch_glob)
    patches.sort()

    return ' '.join(['file://' + patch[len(files_dir)+1:] for patch in patches])

SRC_URI += " \
    git://github.com/TobiasSchaffner/linux.git;protocol=https;branch=tobsch/JH7110_VisionFive2_preempt_rt;destsuffix=linux-visionfive-${PV} \
    file://starfive_visionfive2_defconfig \
    file://starfive2_extra.cfg \
    file://preempt-rt.cfg \
    file://add-nmi-callback-and-raw-parport-driver.patch \
    file://latency-histograms.patch \
    file://net-ipv4-icmp-ping-sysrq.patch \
    file://save-current-patchset-in-kernel.patch \
    file://sched-add-per-cpu-load-measurement.patch \
    "

SRCREV = "dfa52cc14f3b4a4a9a4827aa7cbd12830832d68c"

S = "${WORKDIR}/linux-visionfive-${PV}"

KERNEL_DEFCONFIG = "starfive_visionfive2_defconfig"

LINUX_VERSION_EXTENSION = "-isar"
