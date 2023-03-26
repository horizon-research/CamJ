# Computational CIS Modeled Using CamJ

This directory contains all the examples we used in the original ISCA 2023 paper for validating and show-casing the capabilities of CamJ. In total, we modeled nine computational CIS as listed below. The first nine papers are used for validation and the last two are used as CamJ use-cases.

* [`isscc_17_0_62`](https://github.com/horizon-research/CamJ/tree/main/examples/isscc_17_0_62):  [A 0.62mW Ultra-Low-Power Convolutional-NeuralNetwork Face-Recognition Processor and a CIS Integrated with Always-On Haar-Like Face Detector](https://ieeexplore.ieee.org/abstract/document/7870354) (ISSCC 2017).
* [`jssc_19`](https://github.com/horizon-research/CamJ/tree/main/examples/jssc_19):  A Data-Compressive 1.5/2.75-bit Log-Gradient QVGA Image Sensor With Multi-Scale Readout for Always-On Object Detection. [(Link)](https://ieeexplore.ieee.org/document/8844721)
* [`sensors_20`](https://github.com/horizon-research/CamJ/tree/main/examples/sensors_20):  Design of an Always-On Image Sensor Using an Analog Lightweight Convolutional Neural Network. [(Link)](https://www.mdpi.com/1424-8220/20/11/3101)
* [`isscc_21_back_illuminated`](https://github.com/horizon-research/CamJ/tree/main/examples/isscc_21_back_illuminated): A 1/2.3inch 12.3Mpixel with On-Chip 4.97TOPS/W CNN Processor Back-Illuminated Stacked CMOS Image Sensor. [(Link)](https://ieeexplore.ieee.org/document/9365965)
* [`jssc21_05v`](https://github.com/horizon-research/CamJ/tree/main/examples/jssc21_05v): A 0.5-V Real-Time Computational CMOS Image Sensor With Programmable Kernel for Feature Extraction. [(Link)](https://ieeexplore.ieee.org/document/9250500)
* [`jssc21_51pj`](https://github.com/horizon-research/CamJ/tree/main/examples/jssc21_51pj): A 51-pJ/Pixel 33.7-dB PSNR 4× Compressive CMOS Image Sensor With Column-Parallel Single-Shot Compressive Sensing. [(Link)](https://ieeexplore.ieee.org/document/9424987)
* [`vlsi_21`](https://github.com/horizon-research/CamJ/tree/main/examples/vlsi_21): A 2.6 e-rms Low-Random-Noise, 116.2 mW Low-Power 2-Mp Global Shutter CMOS Image Sensor with Pixel-Level ADC and In-Pixel Memory. [(Link)](https://ieeexplore.ieee.org/document/9492357)
* [`isscc_22_08v`](https://github.com/horizon-research/CamJ/tree/main/examples/isscc_22_08v): A 0.8V Intelligent Vision Sensor with Tiny Convolutional Neural Network and Programmable Weights Using Mixed-Mode Processing-in-Sensor Technique for Image Classification. [(Link)](https://ieeexplore.ieee.org/document/9731675)
* [`tcas_i22`](https://github.com/horizon-research/CamJ/tree/main/examples/tcas_i22): Senputing: An Ultra-Low-Power Always-On Vision Perception Chip Featuring the Deep Fusion of Sensing and Computing. [(Link)](https://ieeexplore.ieee.org/document/9464962)
* [`ieee_vr22`](https://github.com/horizon-research/CamJ/tree/main/examples/ieee_vr22): Real-Time Gaze Tracking with Event-Driven Eye Segmentation. [(Link)](https://arxiv.org/abs/2201.07367)
* [`rhythmic_pixel_21`](https://github.com/horizon-research/CamJ/tree/main/examples/rhythmic_pixel_21): Rhythmic Pixel Regions: Multi-resolution Visual Sensing System
towards High-Precision Visual Computing at Low Power. [(Link)](https://meteor.ame.asu.edu/publications/asplos21_rhythmic_pixel_regions.pdf)

The table below summarizes the high-level hardware specifications of the CIS we modeled, which covers a wide variety of design variations. Unit of analog memory size is “number of analog values”.

<table>
    <tr>
        <th rowspan="2">Case Name</th>
        <th rowspan="2">Stacked</th>
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
        <td>isscc_17_0_62</td>
        <td>No</td>
        <td>3T APS</td>
        <td>20x80</td>
        <td>Avg. & Add</td>
        <td>Column & Chip</td>
        <td>Charge & Voltage</td>
        <td>160KB</td>
        <td>4x4x64</td>
    </tr>
    <tr>
        <td>jssc_19</td>
        <td>No</td>
        <td>4T APS</td>
        <td>4x240</td>
        <td>Logarithmic Sub.</td>
        <td>Column</td>
        <td>Voltage</td>
        <td>-</td>
        <td>-</td>
    </tr>
    <tr>
        <td>sensors_20</td>
        <td>No</td>
        <td>4T APS</td>
        <td>No</td>
        <td>MAC</td>
        <td>Column</td>
        <td>Voltage</td>
        <td>-</td>
        <td>-</td>
    </tr>
    <tr>
        <td>isscc_21_back_illuminated</td>
        <td>Yes</td>
        <td>4T APS</td>
        <td>No</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td>8MB</td>
        <td>1x2304</td>
    </tr>
    <tr>
        <td>jssc_21_05v</td>
        <td>No</td>
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
        <td>Yes</td>
        <td>4T APS</td>
        <td>No</td>
        <td>MAC</td>
        <td>Column</td>
        <td>Charge</td>
        <td>-</td>
        <td>-</td>
    </tr>
    <tr>
        <td>vlsi_21</td>
        <td>No</td>
        <td>DPS</td>
        <td>No</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td>6MB</td>
        <td>-</td>
    </tr>
    <tr>
        <td>isscc_22_08v</td>
        <td>No</td>
        <td>PWM</td>
        <td>No</td>
        <td>MAC</td>
        <td>Column</td>
        <td>Time & Current</td>
        <td>256B</td>
        <td>1</td>
    </tr>
    <tr>
        <td>tcas_i22</td>
        <td>No</td>
        <td>3T APS</td>
        <td>No</td>
        <td>Mul. & Add</td>
        <td>Pixel & Chip</td>
        <td>Current</td>
        <td>-</td>
        <td>-</td>
    </tr>
    <tr>
        <td>ieee_vr22</td>
        <td>No</td>
        <td>3T APS</td>
        <td>201x320</td>
        <td>Mul. & Abs. Diff.</td>
        <td>Column</td>
        <td>Voltage</td>
        <td>64K</td>
        <td>16x16</td>
    </tr>
    <tr>
        <td>rhythmic_pixel_21</td>
        <td>No</td>
        <td>3T APS</td>
        <td>No</td>
        <td>-</td>
        <td>-</td>
        <td>-</td>
        <td>2560B</td>
        <td>1x16</td>
    </tr>
</table>

## How to run

Use `example_run.py` to run all the examples:
```
 $ python example_run.py
```

Run with `--help` to see how to run each example individually:
```
 $ python example_run.py --help

optional arguments:
  -h, --help       show this help message and exit
  --isscc_17_0_62  Run ISSCC 17 0.62V example
  --jssc_19        Run JSSC 19 example
  --sensors_20     Run Sensors 20 example
  --isscc_21       Run ISSCC 21 Back-illuminated example
  --jssc21_05v     Run JSSC 21 0.5V example
  --jssc21_51pj    Run JSSC 21 51pJ example
  --vlsi_21        Run VLSI 21 example
  --isscc_22_08v   Run ISSCC 22 0.8V example
  --tcas_i22       Run TCAS-I 22 example
  --ieee_vr22      Run IEEE VR22 example
  ...
  
```

Alternatively, you can run `python run.py` in each sub-directory.
