# Real-Time Linux evaluation images


This isar layer allows to build debian based real-time evaluation images for the StarFive VisionFive2 and the Raspberry Pi 4, using either PREEMPT_RT or EVL (Xenomai 4).


The images include:
 * A custom kernel with the PREEMPT_RT patch or EVL (Dovetail) applied
 * Some realtime tuning
 * Realtime evaluation tools
 * OSADL patches and tools needed to integrate it in the OSADL QA farm


Find the latency plots generated in the OSADL QA farm here: https://www.osadl.org/Latency-plot-of-system-in-rack-3-slot.qa-latencyplot-r3s2.0.html?shadow=1


## Build

A container engine like podman or docker has to be installed.


Run kas-container to build the desired image:
```
./kas-container --isar build kas/<target>.yml
```


Supported targets:
 * raspberry-pi4-preemptrt
 * raspberry-pi4-evl
 * starfive-visionfive2-1.2a-preemptrt
 * starfive-visionfive2-1.2a-evl
 * starfive-visionfive2-1.3b-preemptrt
 * starfive-visionfive2-1.3b-evl

Optional overlays:
 * opt-debug - Enable EVL/kernel debug options


Alternatively you can download the latest images from: https://github.com/TobiasSchaffner/isar-osadl-rt-testing-images/actions
