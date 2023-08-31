# This software is a part of ISAR.
# Copyright (C) 2022 ilbers GmbH

DESCRIPTION = "Boot config for Raspberry PI boards"
MAINTAINER = "isar-users <isar-users@googlegroups.com>"

SRC_URI = "file://config.txt.tmpl \
	   file://cmdline.txt.tmpl"

inherit dpkg-raw

TEMPLATE_VARS = "MACHINE_SERIAL BAUDRATE_TTY IMAGE_KERNEL_CMDLINE_TUNE KERNEL_FILE KERNEL_VERSION"
TEMPLATE_FILES = "config.txt.tmpl cmdline.txt.tmpl"

do_install() {
    install -v -d ${D}/boot/
    install -v -m 644 ${WORKDIR}/config.txt ${D}/boot/
    install -v -m 644 ${WORKDIR}/cmdline.txt ${D}/boot/
}
