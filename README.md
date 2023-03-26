# CamJ: An Energy Modeling and System-Level Exploration Framework for In-Sensor Visual Computing

At its core, CamJ simulates the noise and energy consumption of an CMOS Image Sensor (CIS) in seconds under a Frame Per Second (FPS) target.
CamJ allow users to describe the CIS hardware, both the analog and digital components, and the (imaging, image processing, and computer vision) algorithm to be executed on the CIS using a declarative interface in Python.
Under the surface, CamJ models the interplay across main structures of a computational CIS pipeline: pixel sensing → analog processing → digital processing.
Thus, CamJ enables end-to-end modeling and optimization of the CIS architecture from photon ingestion to semantic results.

## Code Organization

- `camj`: the source code of CamJ. If you want to contribute to the project, this is where your main coding activities will be.
- `tutorial`: a step-by-step tutorial showing you how to use the CamJ APIs to model a simple computational image sensor and obtain its noise and energy consumption estimations.
- `utility`: useful tools, e.g., generating noise-free images (input to CamJ) from RGB images.
- `examples`: existing computational image sensors that we modeled using CamJ and validated against published/measured results.
- `tests`: test cases.
- `test_imgs`: sample inputs to CamJ, i.e., noise-free images.

## Documentation

The documentation is hosted [here](https://camj.readthedocs.io/en/latest/).

## Installing CamJ

The code is written entirely in Python, and requires minimal external packages, which are all listed in `requirements.txt` or `requirements.yml`. We recommend to use package management system like `Conda`. 
Install the packages that CamJ relies on by running `conda env create -f requirements.yml` via `Conda`.
You can also install packages via `pip` by runnning `pip install -r requirements.txt`.
As with any Python project, we recommend creating a [virtual environment](https://docs.python.org/3/library/venv.html) (or other alternatives). 

## What is CamJ Useful For?

CamJ is meant to be used for *system-level* exploration after each component design is sketched out;
an analogy would be Systems-on-a-Chip (SoC) vs. accelerator design.
Before system-level exploration, a team usually has at hand a range of component-level designs, which could be licensed Intellectual Property (IP) blocks, reference designs from the literature, or earlier designs from other teams in the organization;
in all cases the component-level energy behavior is known or can be modeled using external tools.

CamJ helps designers make design decisions when assembling the individual (digital and analog) components into an optimal system.
Ideally, a designer uses CamJ to estimate the system energy given initial designs of individual components; using the estimation, a designer can iteratively refine the components/system design.
For instance, CamJ can identify energy bottlenecks and guide the re-design of corresponding components.
Orthogonally, a designer can use CamJ to explore optimal mapping and partitioning of the algorithms between analog vs. digital domains or in vs. off CIS to minimize overall system energy under performance targets.

CamJ is *not* a synthesis tool; it does not generate a digital accelerator (or analog circuits for that matter), which is the goal of a High-Level Synthesis (HLS) tool.
Rather, CamJ can be used in conjunction with HLS: one could use HLS to first generate an accelerator and then use CamJ to explore, in the
bigger system, how/whether that accelerator would fit in a computational CIS to maximize end-to-end application gains.

## Citation

```
@inproceedings{ma2023camj,
  title={CamJ: Enabling System-Level Energy Modeling and Architectural Exploration for In-Sensor Visual Computing},
  author={Ma, Tianrui and Feng, Yu and Zhang, Xuan and Zhu, Yuhao},
  booktitle={Proceedings of the 50th Annual International Symposium on Computer Architecture},
  year={2023}
}
```
