#
# Copyright (c) Siemens AG, 2023
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

require osadl-rt-test-image-common.inc

IMAGE_PREINSTALL += "stress-ng"

# Realtime tooling
IMAGE_INSTALL += "libevl-test"
