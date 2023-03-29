What Are Supported by CamJ?
==============================

**CamJ** provides a high-level interface that describes some commonly-used analog and digital
structures. Users can directly plog-in those APIs in their image sensor designs. Here we summarize
these hareware structures.

Analog Domain
----------------------

The figure shown below presents all the analog components that are supported by **CamJ**.

.. image:: imgs/supported_ops.png
    :width: 2000

In this figure, the top level shows the algorithmic operations that are currently supported in
**CamJ**. The second level shows the possible analog components that support the algorithmic
operations. The bottom level shows the major basic analog components that compose the analog
components at the second level. Both the energy and noise modeling in **CamJ** are performed in
the analog components at the bottom level.

The table below shows the overview of analog components at the second level.

.. raw:: html
    :file: analog_table.html