#
# Copyright (c) Siemens AG, 2023
#
# Authors:
#  Tobias Schaffner <tobias.schaffner@siemens.com>
#
# SPDX-License-Identifier: MIT

require osadl-rt-test-image-common.inc

# Realtime tooling
IMAGE_PREINSTALL += "rt-tests jitterdebugger stress-ng"
