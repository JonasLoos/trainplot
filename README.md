# trainplot

Dynamically updating plots in Jupyter notebooks, e.g. for visualizing training progress. Inspired by [livelossplot](https://github.com/stared/livelossplot), and aims to be easier to use with better jupyter notebook support.

Trainplot outputs the matplotlib figure to an `ipywidgets.Output` widget, so it doesn't interfere with other outputs like `tqdm` or print statements. To avoid wasting resources and flickering, the figure is only updated with a given `update_period`.


## Installation

```bash
pip install trainplot
```


## Usage

Trainplot is designed to be used in Jupyter notebooks.

This is a simple example ([example notebook](examples/basic-example.ipynb)):

```python
from trainplot import plot
from time import sleep

for i in range(100):
    plot(i = i+random.random()*10, root = i**.5*3)
    sleep(0.1)
```

<img src="https://github.com/JonasLoos/trainplot/assets/33965649/614f8ed4-8646-4100-b869-187ea89f1bb2" width="500">

---

There is a tf/keras callback ([example notebook](examples/tf-keras-mnist-example.ipynb)):

```python
from trainplot import TrainPlotKeras

model = ...
model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=10, callbacks=[TrainPlotKeras()])
```

<img src="https://github.com/JonasLoos/trainplot/assets/33965649/4ddff79a-978e-434c-a6c3-571cf48c0892" width="500">

---

It also works together with e.g. `tqdm.notebook` and printing ([example notebook](examples/different-output-example.ipynb)):

```python
from trainplot import plot
from tqdm.notebook import trange
from time import sleep

for i in trange(50):
    plot(i=i, root=i**.5)
    if i % 10 == 0:
        print(f'currently at {i} iterations')
    sleep(0.1)
```

<img src="https://github.com/JonasLoos/trainplot/assets/33965649/7571efab-7a3f-4414-b537-a2dffd9e1bec" width="400">

---

You can make use of a TrainPlot object to add a bunch of custumizations ([example notebook](examples/4plots-example.ipynb)):

```python
from trainplot import TrainPlot
from time import sleep

tp = TrainPlot(
    update_period=.2,
    fig_args=dict(nrows=2, ncols=2, figsize=(10, 8), gridspec_kw={'height_ratios': [1, 1], 'width_ratios': [1, 1]}),
    plot_pos={'loss': (0, 0, 0), 'accuracy': (0, 1, 0), 'val_loss': (1, 0, 0), 'val_accuracy': (1, 1, 0)},
    plot_args={'loss': {'color': 'orange'}, 'accuracy': {'color': 'green'}, 'val_loss': {'color': 'orange', 'label': 'validation loss'}, 'val_accuracy': {'color': 'green', 'label': 'validation accuracy'}},
)

for i in range(100, 200):
    tp(step=i, loss=(i/100-2)**4, accuracy=i/2, val_loss=(i/100-2.1)**4, val_accuracy=i/2.1)
    sleep(0.1)
```

<img src="https://github.com/JonasLoos/trainplot/assets/33965649/599314e2-d1c1-4044-a915-6316722a2324" width="600">

When using a Trainplot object, you can also put the plot into a separate cell than the training loop ([example notebook](examples/separate-output-example.ipynb))

---

There is also support for [threading](examples/threading-example.ipynb) to improve runtime performance by parallelization.
