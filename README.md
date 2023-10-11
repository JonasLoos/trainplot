# trainplot

Dynamically updating plots in Jupyter notebooks, e.g. for visualizing training progress. Inspired by [livelossplot](https://github.com/stared/livelossplot)

## Installation

```bash
pip install trainplot
```

## Usage

In your Jupyter notebook import it using:

```python
from trainplot import TrainPlot
```

Then you can use it like this:

```python
trainplot = TrainPlot()

for i in range(100):
    trainplot(i = i+random.random()*10, root = i**.5*3)
    time.sleep(0.1)

trainplot.close()
```

It also works with `tqdm` and printing:

```python
trainplot = TrainPlot()

for i in trange(50):
    trainplot(i=i, root=i**.5)
    if i % 10 == 0:
        print(f'currently at {i} iterations')
    time.sleep(0.1)

trainplot.close()
```

You can also add a bunch of custumizations, e.g.:

```python
from trainplot import TrainPlot
import time

trainplot = TrainPlot(
    update_period=.2,
    fig_args=dict(nrows=2, ncols=2, figsize=(10, 8), gridspec_kw={'height_ratios': [1, 1], 'width_ratios': [1, 1]}),
    plot_pos={'loss': (0, 0, 0), 'accuracy': (0, 1, 0), 'val_loss': (1, 0, 0), 'val_accuracy': (1, 1, 0)},
    plot_args={'loss': {'color': 'orange'}, 'accuracy': {'color': 'green'}, 'val_loss': {'color': 'orange', 'label': 'validation loss'}, 'val_accuracy': {'color': 'green', 'label': 'validation accuracy'}},
)

for i in range(100, 200):
    trainplot(step=i, loss=(i/100-2)**4, accuracy=i/2, val_loss=(i/100-2.1)**4, val_accuracy=i/2.1)
    time.sleep(0.1)

trainplot.close()
```
