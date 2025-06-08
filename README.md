# trainplot

Dynamically updating plots in Jupyter notebooks, e.g. for visualizing training progress. Inspired by [livelossplot](https://github.com/stared/livelossplot), with better Jupyter notebook support and minimal dependencies.

```bash
pip install trainplot
```

<img src="https://github.com/JonasLoos/trainplot/assets/33965649/935e8d52-0c37-4469-9cb8-24fa77b467ff" width="500">


## Usage

Simple example ([example notebook](examples/basic-example.ipynb)):

```python
from trainplot import plot
from time import sleep

for i in range(50):
    plot(loss = 1/(i+1), acc = 1-1/(.01*i**2+1))
    sleep(.1)
```

Example for the tf/keras callback ([example notebook](examples/tf-keras-mnist-example.ipynb)):

```python
from trainplot import TrainPlotKeras

model = ...
model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=10, callbacks=[TrainPlotKeras()])
```


## Features

* **Lightweight**: No external plotting dependencies
* **Custom rendering**: Uses HTML5 Canvas for fast, smooth updates
* **Multiple series**: Automatically handles multiple data series with different colors
* **Real-time updates**: Configurable update periods to balance performance and responsiveness
* **Keras support**: Built-in callback for TensorFlow/Keras models

## How it works

Trainplot uses a custom HTML5 Canvas-based plotting solution that renders directly in Jupyter notebooks. To avoid wasting resources and flickering, the plot is only updated with a given `update_period`. A `post_run_cell` callback is added to the `IPython` instance, so that all updated TrainPlot figures include all new data when a cell execution is finished. When using `trainplot.plot`, a TrainPlot object is created for the current cell.
