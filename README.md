# preempt_rt evaluation images with osadl additions

This isar layer allows to build debian based preempt_rt evaluation images for the starfive visionfive2 and the raspberry pi 4.

## Build

```
wget https://raw.githubusercontent.com/siemens/kas/master/kas-container
chmod +x kas-container
./kas-container build <board_name>.yml
```
