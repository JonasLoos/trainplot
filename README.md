# trainplot

Dynamically updating plots in Jupyter notebooks, e.g. for visualizing machine learning training progress.

```bash

pip install trainplot
```

<p align="center"><img src="https://github.com/user-attachments/assets/03bd661c-37d7-41a4-ba91-891f57ebfcf8" width="400" center></p>



## Usage

Basic usage:

```python
from trainplot import plot

for i in range(100):
    loss = ...
    acc = ...
    plot(loss=loss, accuracy=acc)
```

If you use keras, you can use the `TrainPlotKerasCallback`:

```python
from trainplot import TrainPlotKeras

model = ...
model.fit(x_train, y_train, validation_data=(x_test, y_test), epochs=10, callbacks=[TrainPlotKerasCallback()])
```

For more examples, see the [`examples`](examples/) folder.


## Features

* **Lightweight**: No external plotting dependencies
* **Custom rendering**: Uses HTML5 Canvas for fast, smooth updates
* **Multiple series**: Automatically handles multiple data series with different colors
* **Real-time updates**: Configurable update periods to balance performance and responsiveness
* **Keras support**: Built-in callback for TensorFlow/Keras models


## How it works

Trainplot uses a custom HTML5 Canvas-based plotting solution that renders directly in Jupyter notebooks. To avoid wasting resources and flickering, the plot is only updated with a given `update_period`. A `post_run_cell` callback is added to the `IPython` instance, so that all updated TrainPlot figures include all new data when a cell execution is finished. When using `trainplot.plot`, a TrainPlot object is created for the current cell.
