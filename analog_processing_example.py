import numpy as np
import analog_function_set

AFS = analog_function_set.AFS()

# ComputeSum (4x4 block in analog domain)

# user define
###computation model
# operation
#input-output
x = np.random.randint(0, 256, size=(16,))

###hardware domain
#signal domain
# operation throughput

##mapping file

# simulator outputs
energy = 0
delay = 0
area = 0
sum_ = 0

for i in range(16):
    x_, energy_, delay_ = AFS.read(x[i])
    energy = energy + energy_
    delay = delay + delay_

    if i == 0:
        sum_ = x_.copy()
    else:
        sum_, energy_, delay_ = AFS.add(sum_, x_)
        energy = energy + energy_
        delay = delay + delay_

print("ComputeSum (4x4 block in analog domain):", sum_, energy, delay, area)
