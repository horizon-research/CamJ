.. CamJ documentation master file, created by
   sphinx-quickstart on Thu Mar 16 13:44:31 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

CamJ
================================

At its core, **CamJ** simulates the noise and energy consumption of an CMOS Image Sensor (CIS) in seconds under a Frame Per Second (FPS) target.
**CamJ** allow users to describe the CIS hardware, both the analog and digital components, and the (imaging, image processing, and computer vision) algorithm to be executed on the CIS using a declarative interface in Python.
Under the surface, **CamJ** models the interplay across main structures of a computational CIS pipeline: pixel sensing → analog processing → digital processing.
Thus, **CamJ** enables end-to-end modeling and optimization of the CIS architecture from photon ingestion to semantic results.


Cite Us
------------------------------

To know more about **CamJ**, please check out our `paper <https://horizon-lab.org/pubs.html>`_ and cite us::

    @inproceedings{ma2023camj,
      title={CamJ: Enabling System-Level Energy Modeling and Architectural Exploration for In-Sensor Visual Computing},
      author={Ma, Tianrui and Feng, Yu and Zhang, Xuan and Zhu, Yuhao},
      booktitle={Proceedings of the 50th Annual International Symposium on Computer Architecture},
      year={2023}
    }

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   intro
   tutorial
   camj

