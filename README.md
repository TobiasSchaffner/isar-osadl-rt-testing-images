# preempt_rt evaluation images with osadl additions

This isar layer allows to build debian based preempt_rt evaluation images for the starfive visionfive2 and the raspberry pi 4.

## Prerequisites

A container engine like podman or docker has to be installed.

## Build

Run kas-container to build the desired image:
```
./kas-container build kas/<target>.yml
```

Supported targets:
 * raspberry-pi4-kernel-5.15-rt
 * raspberry-pi4-kernel-6.6-rt
 * starfive-visionfive2-1.2a-kernel-6.6-rt
 * starfive-visionfive2-1.3b-kernel-5.15-rt
 * starfive-visionfive2-1.3b-kernel-6.6-rt
