# trainplot

Dynamically updating plots in Jupyter notebooks, e.g. for visualizing training progress. Inspired by [livelossplot](https://github.com/stared/livelossplot), and aims to be easier to use with better jupyter notebook support.


## Installation

```bash
pip install trainplot
```


## Usage

This is a simple example ([example notebook](examples/basic-example.ipynb)):

```python
from trainplot import plot
from time import sleep

for i in range(50):
    plot(loss = 1/(i+1), acc = 1-1/(.01*i**2+1))
    sleep(.1)
```

<img src="https://github.com/JonasLoos/trainplot/assets/33965649/935e8d52-0c37-4469-9cb8-24fa77b467ff" width="500">

---

Example for the tf/keras callback ([example notebook](examples/tf-keras-mnist-example.ipynb)):

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

---

More:
* When using a Trainplot object, you can also put the plot into a separate cell than the training loop ([example notebook](examples/separate-output-example.ipynb))
* There is also support for [threading](examples/threading-example.ipynb) to improve runtime performance by parallelization.


## How it works

Trainplot outputs the matplotlib figure to an `ipywidgets.Output` widget, so it doesn't interfere with other outputs like `tqdm` or print statements. To avoid wasting resources and flickering, the figure is only updated with a given `update_period`. This can also be done from a separate `threading.Thread`, to not block the main thread.
A `post_run_cell` callback is added to the `IPython` instance, so that all updated TrainPlot figures include all new data when a cell execution is finished.
When using `trainplot.plot`, a TrainPlot object is created for the current cell and cell-execution-count.
