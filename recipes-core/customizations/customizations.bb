#
# Copyright (c) Siemens AG, 2023
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

inherit dpkg-raw

DESCRIPTION = "image customizations"

SRC_URI = "file://postinst \
           file://ethernet \
           file://dhclient.service \
           file://80-sshd-root-login.conf"

DEBIAN_DEPENDS = "ifupdown, \
                  isc-dhcp-client, \
                  net-tools, \
                  iputils-ping, \
                  ssh, \
                  sshd-regen-keys"

do_install() {
	install -v -d ${D}/etc/network/interfaces.d
	install -v -m 644 ${WORKDIR}/ethernet ${D}/etc/network/interfaces.d/

    install -v -d ${D}/etc/ssh/sshd_config.d/
    install -v -m 644 ${WORKDIR}/80-sshd-root-login.conf ${D}/etc/ssh/sshd_config.d/

    install -v -d ${D}/etc/systemd/system/
    install -v -m 644 ${WORKDIR}/dhclient.service ${D}/etc/systemd/system/
}
