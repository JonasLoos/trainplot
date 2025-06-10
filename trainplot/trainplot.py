import time
from collections import defaultdict
from IPython.display import display
from IPython import get_ipython
import numpy as np
import anywidget
import traitlets
from .plotting_function import js_code


class TrainPlotWidget(anywidget.AnyWidget):
    """A custom widget for training plots that renders using HTML5 Canvas."""

    # Synchronized state between Python and JavaScript
    data = traitlets.Dict({}).tag(sync=True)
    reduction_factor = traitlets.Int(1).tag(sync=True)
    max_step = traitlets.Int(0).tag(sync=True)
    width = traitlets.Int(600).tag(sync=True)
    height = traitlets.Int(400).tag(sync=True)
    _esm = js_code


class TrainPlot:
    """Main TrainPlot class for monitoring training progress."""

    def __init__(self, update_period: float = 0.1, width: int = 600, height: int = 400, max_points: int = 100):
        """Create a TrainPlot instance."""
        if update_period < 0:
            raise ValueError(f'update_period must be positive, got {update_period}')
        if max_points < 2:
            raise ValueError(f'max_points must be at least 2, got {max_points}')
        if max_points % 2 != 0:
            raise ValueError(f'max_points must be even, got {max_points}')

        self.update_period = update_period
        self.max_points = max_points
        self.data: "dict[str, np.ndarray]" = {}
        self.counts: "dict[str, np.ndarray]" = {}
        self.current_step = -1
        self.max_step = 0
        self.reduction_factor = 1
        self.last_update_time = 0

        # Create anywidget instance
        self.widget = TrainPlotWidget(width=width, height=height)

        if ENV.ipython_instance is not None:
            display(self.widget)

    def update(self, step: "int | None" = None, **kwargs):
        """Update the data, which will be plotted as soon as `update_period` has passed since the last plot.

        You can also call the TrainPlot object directly, which is equivalent to calling this function.

        Args:
            NAME=NEW_VALUE, ...
                Where NAME is the name of the data to update and NEW_VALUE is the new value to append to the data list.
                If NAME is 'step', NEW_VALUE is used as x value instead of the internal step counter.

        Examples:
            trainplot.update(loss=0.1, accuracy=0.9)
            # or
            trainplot(step=10, loss=0.05, accuracy=0.95)
        """
        if step is None:
            step = self.current_step + 1
        self.current_step = step
        self.max_step = max(self.max_step, step)
        i = step // self.reduction_factor

        # add missing keys
        for key in kwargs.keys():
            if key != 'step' and key not in self.data:
                self.data[key] = np.full(self.max_points, np.nan, dtype=np.float32)
                self.counts[key] = np.full(self.max_points, 0, dtype=np.int32)

        # reduce data to first half if max_step is reached
        if i >= self.max_points:
            self.reduction_factor *= 2
            i = step // self.reduction_factor
            for key in self.data:
                self.data[key][:self.max_points//2] = np.nanmean([self.data[key][::2], self.data[key][1::2]], axis=0)
                self.counts[key][:self.max_points//2] = self.counts[key][::2] + self.counts[key][1::2]
                self.data[key][self.max_points//2:] = np.nan
                self.counts[key][self.max_points//2:] = 0
        for key in self.data:
            if key in kwargs:
                self.counts[key][i] += 1
                c = self.counts[key][i]
                self.data[key][i] = kwargs[key] if c == 1 else (c-1)/c * self.data[key][i] + 1/c * kwargs[key]

        if time.time() - self.last_update_time > self.update_period:
            self.last_update_time = time.time()
            self.update_plot()

        ENV.currently_active_trainplot_objects.add(self)

    def update_plot(self):
        """Update the plot with the current data."""
        if ENV.ipython_instance is not None:
            data_length = self.max_step // self.reduction_factor + 1
            data = {key: self.data[key][:data_length].tolist() for key in self.data}

            # Update widget state and trigger a re-render in JavaScript
            self.widget.data = data
            self.widget.reduction_factor = self.reduction_factor
            self.widget.max_step = self.max_step
            self.widget.send({'render': True})

    def __call__(self, **kwargs):
        """Shortcut for update function."""
        self.update(**kwargs)

    def close(self):
        """Do a final plot update."""
        self.update_plot()


class Plot:
    """Create or update a plot for the current cell."""

    def __init__(self):
        self.line_plots = defaultdict(lambda: TrainPlot())

    def __len__(self):
        return len(self.line_plots)

    def __call__(self, **kwargs):
        """Create or update a plot for the current cell."""
        self.line(**kwargs)

    def line(self, **kwargs):
        """Create or update a line plot for the current cell."""
        if ENV.ipython_instance is None:
            return

        key = (ENV.ipython_instance.execution_count, *kwargs.keys())
        self.line_plots[key].update(**kwargs)


class TrainPlotEnvironmentManager:
    """Manage global variables and IPython hooks"""

    def __init__(self):
        self.ipython_instance = get_ipython()
        if self.ipython_instance is not None:
            self.ipython_instance.events.register('post_run_cell', self.close_ipython_cell)
        else:
            print('WARNING: It seems you are running trainplot outside of an IPython environment. No plots will be displayed.')

        self.currently_active_trainplot_objects: set[TrainPlot] = set()

    def close_ipython_cell(self, *args, **kwargs):
        """Close all TrainPlot objects that were updated in the current cell."""
        for tp in self.currently_active_trainplot_objects:
            tp.close()
        self.currently_active_trainplot_objects.clear()


# Global instances
ENV = TrainPlotEnvironmentManager()
plot = Plot()
