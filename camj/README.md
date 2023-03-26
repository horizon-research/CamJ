# Code Structure

The API documentation is [here](https://camj.readthedocs.io/en/latest/camj/). Briefly, the code structure is:

- `analog`: implementation of analog components, including functional and energy models
- `digital`: implementation of digital components (compute units and memory structures), including latency and energy models; note CamJ doesn't perform functional simulation int the digital domain
- `sw`: interfaces for describing (stencil-based) algorithms
- `general`: constants and high-level simulation functions
