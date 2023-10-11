# trainplot

Dynamically updating plots in Jupyter notebooks, e.g. for visualizing training progress.

## Installation

```bash
pip install trainplot
```

## Usage

In your Jupyter notebook:

```python
from trainplot import TrainPlot
import time

trainplot = TrainPlot()

for i in range(100):
    trainplot(i=i, root=i**.5)
    time.sleep(0.1)
```
