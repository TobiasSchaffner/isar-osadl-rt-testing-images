#
# Copyright (c) Siemens AG, 2025
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

require recipes-core/images/isar-image-base.bb
IMAGE_INSTALL += "customizations sshd-regen-keys expand-on-first-boot"

# Common tooling
IMAGE_PREINSTALL += "vim openssh-server"

# OSADL test image requirements
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
    make \
    munin-node \
    munin-node \
    nasm \
    netpbm \
    openntpd \
    rsync \
    rsyslog \
    snmp"
