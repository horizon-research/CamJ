# Validation Examples

This directory lists all the examples that we use in our paper validation and evaluation. Please 
check each subdirectory for more details.

Here are the directory names with corresponding papers.

* [`ieee_vr22`](https://github.com/horizon-research/CamJ/tree/main/examples/ieee_vr22): Real-Time Gaze Tracking with Event-Driven Eye Segmentation. [(Link)](https://arxiv.org/abs/2201.07367)
* [`isscc_22_08v`](https://github.com/horizon-research/CamJ/tree/main/examples/isscc_22_08v): A 0.8V Intelligent Vision Sensor with Tiny Convolutional Neural Network and Programmable Weights Using Mixed-Mode Processing-in-Sensor Technique for Image Classification. [(Link)](https://ieeexplore.ieee.org/document/9731675)
* [`jssc21_05v`](https://github.com/horizon-research/CamJ/tree/main/examples/jssc21_05v): A 0.5-V Real-Time Computational CMOS Image Sensor With Programmable Kernel for Feature Extraction. [(Link)](https://ieeexplore.ieee.org/document/9250500)
* [`jssc21_51pj`](https://github.com/horizon-research/CamJ/tree/main/examples/jssc21_51pj): A 51-pJ/Pixel 33.7-dB PSNR 4× Compressive CMOS Image Sensor With Column-Parallel Single-Shot Compressive Sensing. [(Link)](https://ieeexplore.ieee.org/document/9424987)
* [`tcas_i22`](https://github.com/horizon-research/CamJ/tree/main/examples/tcas_i22): Senputing: An Ultra-Low-Power Always-On Vision Perception Chip Featuring the Deep Fusion of Sensing and Computing. [(Link)](https://ieeexplore.ieee.org/document/9464962)

The following table shows what computing domain each paper involves and what kind of simulation each
case has:

<table>
    <tr>
        <th rowspan="2">Case Name</th>
        <th align="center" colspan="5">Analog Domain</td>
        <th align="center" colspan="2">Digital Domain</td>
    </tr>
    <tr>
        <td>Pixel</td>
        <td>Memory</td>
        <td>PE Operation</td>
        <td>PE Position</td>
        <td>Op Domain</td>
        <td>Memory</td>
        <td>PE Size</td>
    </tr>
    <tr>
        <td>ieee_vr22</td>
        <td>3T APS</td>
        <td>201x320</td>
        <td>Mul. & Abs. Diff.</td>
        <td>Column</td>
        <td>Voltage</td>
        <td>64K</td>
        <td>16x16</td>
    </tr>
    <tr>
        <td>isscc_22_08v</td>
        <td>PWM</td>
        <td>No</td>
        <td>MAC</td>
        <td>Column</td>
        <td>Time & Current</td>
        <td>256B</td>
        <td>1</td>
    </tr>
    <tr>
        <td>jssc_21_05v</td>
        <td>PWM</td>
        <td>No</td>
        <td>MAC</td>
        <td>Column</td>
        <td>Time & Current</td>
        <td>-</td>
        <td>-</td>
    </tr>
    <tr>
        <td>jssc_21_51pj</td>
        <td>4T APS</td>
        <td>No</td>
        <td>MAC</td>
        <td>Column</td>
        <td>Charge</td>
        <td>-</td>
        <td>-</td>
    </tr>
    <tr>
        <td>tcas_i22</td>
        <td>3T APS</td>
        <td>No</td>
        <td>Mul. & Add</td>
        <td>Pixel & Chip</td>
        <td>Current</td>
        <td>-</td>
        <td>-</td>
    </tr>
</table>

## How to run

Use `example_run.py` to run different validation cases:
```
 $ python example_run.py
```

To know different run options, run `--help` options, you will see different options:
```
 $ python example_run.py --help

usage: example_run.py [-h] [--ieee_vr22] [--isscc_22_08v] [--jssc21_05v] [--tcas_i22]

optional arguments:
  -h, --help      show this help message and exit
  --ieee_vr22     Run IEEE VR22 example
  --isscc_22_08v  Run ISSCC 22 0.8V example
  --jssc21_05v    Run JSSC 21 0.5V example
  --jssc21_51pj   Run JSSC 21 51pJ example
  --tcas_i22      Run TCAS-I 22 example
  ...
  
```