# Air Sampler Controller GUI

## Introduction
This is a Python GUI (Tkinter) for controlling the Raspberry Pi based air sampler. Two pumps are controlled by a motor driver (DRV8833). With this progarm, one can set up schedules for air sampling. The total flow rate is monitored by a flow sensor (Renesas FS1012-1020) and the analog output is converted using an ADC module (ADS1115). 

---

## Requirements
Raspberry Pi &times; 1 *(Currently worked on 3B & Zero W. Other modules like 3B+, 4B should be okay.)*
ADS1115 &times; 1 *(Using I<sup>2</sup>C protocol.)*
DRV8833 &times; 1 *(Program can be executed without motor driver.)*
FS1012-1020 &times; 1
Micro pumps &times; 2 (3V - 6V)

---

## Installation
Install the program and set up the environment by following the commands: 
```shell
$ git clone https://github.com/asgoshawk/air-sampler-controller.git
$ cd air-sampler-controller
$ python3 -m venv .venv
$ source .venv/bin/activate
$ pip3 install -r requirements.txt
```

If no module named tkinter in your Python 3, install the package by running:
```shell
$ sudo apt install python3-tk
```

---

## Usage
Just execute the main.py:
```shell
$ python3 main.py
```
Make sure that the X window (xserver) has been installed in the Raspberry Pi, if you want to execute the program through SSH connection. The GUI should come out like below:

![GUI window](https://i.imgur.com/VzBa0tC.png =80%x)

### Flow Sensor
In the flow sensor panel, **select the log file location before click the Start Logging button**. It will start recording the TP1 & TP2 of the flow sensor and the flow rate. The flow rate is converted with a polynomial function which is calibrated with a soap bubble flow meter. The fitting curves are shown below.

![Flow rate vs. analog readout](https://i.imgur.com/IDP2HUn.png =80%x)

### Pump
In the pupm panel, two pumps can be activated/deactivated by toggling the ON/OFF button beside the status indicators. The pump tasks can be set up in the right panel. The tasks will be shown in the table. To delete tasks, select the tasks in the table and click "Delete Task" button or click "Delete All" to cancel all the tasks.

![Pump task table](https://i.imgur.com/bbhyL2f.png =80%x)

### Shutdown

Click the X on the top right corner of the window or File > Exit in the toolbar to shutdown all the threads including flow rate logging, pump tasks. The pumps should be turned off at the same time. If the pump still work, execute the following command:

```shell
$ python3 motor_shutdown.py
```