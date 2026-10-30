#
# Copyright (c) Siemens AG, 2025
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

require recipes-core/images/isar-image-base.bb
IMAGE_INSTALL += "customizations sshd-regen-keys expand-on-first-boot"

IMAGE_INSTALL += "unix-bench"
IMAGE_PREINSTALL += "rt-tests stress-ng"

# Memory-interference analysis (paper, Section VI-B)
IMAGE_INSTALL += "isolbench"
# The memlat tools access JH7110 registers through /dev/mem: VisionFive 2 only
IMAGE_INSTALL:append:starfive-visionfive2 = " visionfive2-memlat-tools"

# Common tooling
IMAGE_PREINSTALL += "vim openssh-server htop iperf3"

# Test image requirements
IMAGE_PREINSTALL += "\
    bc \
    bison \
    cron \
    dbus \
    dbus-session-bus-common \
    dbus-system-bus-common \
    flex \
    gcc \
    gpm \
    libelf-dev \
    libncurses5-dev \
    libnet-dns-perl \
    libnuma-dev \
    libssl-dev \
    liblocale-codes-perl \
    logrotate \
    make \
    mtd-utils \
    munin-node \
    nasm \
    netpbm \
    openntpd \
    rsync \
    rsyslog \
    snmp"
