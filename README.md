# PREEMPT_RT on RISC-V evaluation images


This isar layer allows to build debian based preempt_rt evaluation images for the starfive visionfive2 and the raspberry pi 4.


The images include:
 * A custom kernel with the PREEMPT_RT patch applied
 * Some realtime tuning
 * Realtime evaluation tools
 * OSADL patches and tools needed to integrate it in the OSADL QA farm


Find the latency plots generated in the OSADL QA farm here: https://www.osadl.org/Latency-plot-of-system-in-rack-3-slot.qa-latencyplot-r3s2.0.html?shadow=1


## Build

A container engine like podman or docker has to be installed.


Run kas-container to build the desired image:
```
./kas-container build kas/<target>.yml
```


Supported targets:
 * raspberry-pi4-kernel-6.6-rt
 * starfive-visionfive2-1.2a-kernel-6.6-rt
 * starfive-visionfive2-1.3b-kernel-6.6-rt


Alternatively you can download the latest images from: https://github.com/TobiasSchaffner/isar-osadl-rt-testing-images/actions
