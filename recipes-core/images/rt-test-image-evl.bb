#
# Copyright (c) Siemens AG, 2023
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

require rt-test-image-common.inc

IMAGE_PREINSTALL += "stress-ng"

# hackbench; its cyclictest is diverted by cyclictest-latmus
IMAGE_PREINSTALL += "rt-tests"

# Realtime tooling
IMAGE_INSTALL += "libevl-test"
IMAGE_INSTALL += "cyclictest-latmus"
