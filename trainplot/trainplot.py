from typing import Any
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import Output
from IPython.display import display, clear_output
import time
import threading

class TrainPlot():
    def __init__(self, update_period: float = .5, fig_args: dict[str, Any] = {}, plot_pos: dict[str, tuple[int,int,int]] = {}, plot_args: dict[str,dict[str,Any]] = {}):
        '''
        Args:
            update_period: time in seconds between updates
            fig_args: arguments passed to `plt.subplots`
            plot_pos: dictionary mapping data keys to plot positions
                plot_pos[key] = (row, column, twinx)
                row: row index of plot
                column: column index of plot
                twinx: if 1, plot on secondary y-axis
            plot_args: arguments passed to `plt.plot`
        
        Examples:
            trainplot = TrainPlot(update_period=2, fig_args={'figsize': (10, 8)}, plot_pos={'loss': (0, 0, 0), 'accuracy': (0, 0, 1)}, plot_args={'loss': {'color': 'red'}, 'accuracy': {'color': 'blue'}})
            trainplot = TrainPlot(
                fig_args=dict(nrows=2, ncols=2, figsize=(10, 10), gridspec_kw={'height_ratios': [1, 2], 'width_ratios': [1, 1]}),
                plot_pos={'loss': (0, 0, 0), 'accuracy': (0, 1, 0), 'val_loss': (1, 0, 0), 'val_accuracy': (1, 1, 0)}
            )
        '''
        # check arguments
        if update_period <= 0:
            raise ValueError(f'update_period must be positive, got {update_period}')
        for key, value in plot_pos.items():
            if len(value) != 3:
                raise ValueError(f'plot_pos["{key}"] must be a tuple of length 3, got {value}')
            if value[2] not in (0, 1):
                raise ValueError(f'plot_pos[{key}][2] must be 0 or 1, got {value[2]}')
        # setup output widget
        self.out = Output()
        display(self.out)
        with self.out:
            self.fig, axs = plt.subplots(squeeze=False, **fig_args)
            self.axs = np.full((*np.shape(axs), 2), None, dtype=object)
            self.axs[:, :, 0] = axs
            plt.show()
        # setup properties
        self.plot_pos = plot_pos
        self.plot_args = plot_args
        self.update_period = update_period
        self.lines = []
        self.new_data = False
        self.plotting = False
        self.data = dict()
        self.update_step = 0
        self.plot_thread = None
        self.stop_thread = False

    def _update_plot(self):
        '''Update the plot once'''
        # clear axes
        for ax in self.axs.flatten():
            if ax is not None:
                ax.clear()
        # plot data
        for key, value in self.data.items():
            ax = self.axs[self.plot_pos[key]]
            ax.plot(*zip(*value), **self.plot_args[key])
        # update legend
        for ax in self.axs.flatten():
            if ax is not None and len(ax.get_legend_handles_labels()[1]) > 0:
                ax.legend()
        # plot inside the output widget
        with self.out:
            clear_output(wait=True)
            display(self.fig)

    def _update_periodically(self):
        '''Update the plot periodically.'''
        # plot as long as new data is coming in faster than the update period
        while self.new_data:
            self.new_data = False  # possible race condition
            # plot all data
            self._update_plot()
            # wait for next update, while checking if the thread should stop
            for _ in np.arange(0, self.update_period, 0.1):
                if self.stop_thread:
                    break
                time.sleep(0.1)
        self.plotting = False

    def update(self, **args):
        '''Update the data, which will be plotted as soon as `update_period` has passed since the last plot.

        You can also call the TrainPlot object directly, which is equivalent to calling this function.

        Args:
            NAME=NEW_VALUE, ...
                Where NAME is the name of the data to update and NEW_VALUE is the new value to append to the data list.
                If NAME is 'step', NEW_VALUE is used as x value instead of the internal step counter.

        Examples:
            trainplot.update(loss=0.1, accuracy=0.9)
            # or
            trainplot(step=10, loss=0.05, accuracy=0.95)
        '''
        update_step = self.update_step
        for key, value in args.items():
            if key == 'step':
                # use given step instead of internal step counter
                update_step = value
            elif key == 'epoch':
                # TODO: implement epochs
                raise NotImplementedError('Epochs not supported yet')
            elif key not in self.data:
                # create new data list
                self.data[key] = [(update_step, value)]
                # add default plot position
                if key not in self.plot_pos:
                    self.plot_pos[key] = (0, 0, 0)
                # create twinx if necessary
                pos = self.plot_pos[key]
                if pos[2] == 1:
                    self.axs[pos] = self.axs[pos[0],pos[1],0].twinx()
                # add default plot arguments
                if key not in self.plot_args:
                    self.plot_args[key] = {}
                # add default label
                if 'label' not in self.plot_args[key]:
                    self.plot_args[key]['label'] = key
            else:
                # append to existing data list
                self.data[key].append((update_step, value))
        self.update_step += 1
        self.new_data = True

        # Start plotting
        if not self.plotting:
            self.plotting = True  # possible race condition
            self.plot_thread = threading.Thread(target=self._update_periodically)
            self.plot_thread.start()

    def __call__(self, **args):
        '''Shutcut for `update` function.'''
        self.update(**args)

    def close(self):
        '''Do a final plot update.'''
        # prevent waiting, by setting stop_thread to True, which causes the thread to exit as soon as all data is plotted
        self.stop_thread = True
        self.plot_thread.join()



# TODO: TrainPlotKeras
