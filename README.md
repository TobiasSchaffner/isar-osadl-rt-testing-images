# Real-Time Linux evaluation images

This isar layer allows to build debian based real-time evaluation images for the StarFive VisionFive2 and the Raspberry Pi 4, using either PREEMPT_RT or EVL (Xenomai 4) from pinned inputs. Debian packages downloaded from upstream are pinned to the Debian Snapshot defined in ISAR_APT_SNAPSHOT_DATE all custom build packages are pinned with a sha256sum in this repository or in one the the included isar layers.

The images include:
 * A custom kernel with the PREEMPT_RT patch or EVL (Dovetail) applied
 * Realtime tuning
 * Realtime evaluation tools: cyclictest, latmus
 * Tools for load generation: stress-ng, hackbench, unix-bench

## Build

A container engine like podman or docker has to be installed.

Run kas-container to build the desired image:
```
./kas-container --isar build kas/<target>.yml
```

Supported targets:
 * raspberry-pi4-preemptrt
 * raspberry-pi4-evl
 * starfive-visionfive2-preemptrt
 * starfive-visionfive2-evl

Optional overlays:
 * opt-debug - Enable EVL/kernel debug options

Alternatively you can download the latest images from: https://github.com/TobiasSchaffner/isar-osadl-rt-testing-images/actions
