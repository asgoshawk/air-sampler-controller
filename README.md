## Air Sampler Controller GUI

### Introduction
This is a Python GUI (Tkinter) for controlling the Raspberry Pi based air sampler. Two pumps are controlled by a motor driver (DRV8833). With this progarm, one can set up schedules for air sampling. The total flow rate is monitored by a flow sensor (Renesas FS1012-1020) and the analog output is converted using ADS1115 module (I<sup>2</sup>C). 

### Installation
```Shell
git clone https://github.com/asgoshawk/air-sampler-controller.git
cd air-sampler-controller
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
```
### Usage
```Shell
python3 main.py
```