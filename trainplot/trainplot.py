from typing import Any, Callable
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import Output
from IPython.display import display
import time
import threading



class TrainPlotBase():
    def __init__(self, update_period: float, threaded: bool, plot_init_fn: Callable[[], tuple[Any, Any]], plot_update_fn: Callable[[Any, Any, np.ndarray], Any]):
        '''
        Args:
            update_period: minimum time in seconds between plot updates.
            threaded: if `True`, plot in a separate thread. If `False`, plot in the main thread (slower).
                If you experience problems with other output vanishing or ending up in the plot, try setting this to `False`.
            plot_init_fn: function that creates the plot
            plot_update_fn: function that updates the plot
        '''
        # check arguments
        if update_period < 0:
            raise ValueError(f'update_period must be positive, got {update_period}')

        # setup output widget
        self.out = Output()
        display(self.out)
        self.fig, self.init_results = plot_init_fn()
        self.out.append_display_data(self.fig)
        # TODO: fix/limit size of output widget, to prevent flickering

        # setup properties
        self.plot_update_fn = plot_update_fn
        self.update_period = update_period
        self.lines = []
        self.new_data = False
        self.plotting = False
        self.data = dict()
        self.update_step = 0
        self.threaded = threaded
        self.plot_thread = None
        self.stop_thread = False
        self.last_update = 0  # only used if self.threaded is False

    def _update_plot(self):
        self.out.outputs = ()
        self.out.append_display_data(self.plot_update_fn(self.fig, self.init_results, self.data))

    def _update_plot_periodically(self):
        '''Update the plot periodically. This function is made to be called in a separate thread.'''
        # plot as long as new data is coming in faster than the update period
        while self.new_data:
            self.new_data = False  # possible race condition
            self.last_update = time.time()
            # plot all data
            self._update_plot()
            # wait for next update, while checking if the thread should stop
            while time.time() - self.last_update < self.update_period:
                if self.stop_thread:
                    break
                time.sleep(0.05)
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
            else:
                # append to existing data list
                self.data[key].append((update_step, value))
        self.update_step += 1

        # plotting
        if self.threaded:
            # start plotting thread if not already running
            self.new_data = True
            if not self.plotting:
                self.plotting = True  # possible race condition
                self.plot_thread = threading.Thread(target=self._update_plot_periodically)
                self.plot_thread.start()
        else:
            # plot in main thread if enough time has passed since the last plot
            if time.time() - self.last_update > self.update_period:
                self.last_update = time.time()
                self._update_plot()

    def __call__(self, **args):
        '''Shutcut for `update` function.'''
        self.update(**args)

    def close(self):
        '''Do a final plot update.'''
        # prevent waiting, by setting stop_thread to True, which causes the thread to exit as soon as all data is plotted
        if self.threaded:
            self.stop_thread = True
            if self.plot_thread is not None:
                self.plot_thread.join()
        else:
            # final update
            self.plot_update_fn(self.fig, self.init_results, self.data)




class TrainPlot(TrainPlotBase):
    def __init__(self, update_period: float = .5, threaded: bool = True, fig_args: dict[str, Any] = {}, plot_pos: dict[str, tuple[int,int,int]] = {}, plot_args: dict[str,dict[str,Any]] = {}):
        '''
        Args:
            update_period: minimum time in seconds between updates. If 0, plot immediately after each data update.
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
        for key, value in plot_pos.items():
            if len(value) != 3:
                raise ValueError(f'plot_pos["{key}"] must be a tuple of length 3, got {value}')
            if value[2] not in (0, 1):
                raise ValueError(f'plot_pos[{key}][2] must be 0 or 1, got {value[2]}')

        def default_plot_init_fn():
            fig, axs_list = plt.subplots(squeeze=False, **fig_args)
            axs = np.full((*np.shape(axs_list), 2), None, dtype=object)
            axs[:, :, 0] = axs_list
            # create twinx where necessary
            for _, pos in plot_pos.items():
                if pos[2] == 1 and axs[pos[0], pos[1], 0] is None:
                    axs[pos] = axs[pos[0], pos[1], 0].twinx()
            return fig, axs

        def default_plot_update_fn(fig, axs, data: np.ndarray):
            # clear axes
            for ax in axs.flatten():
                if ax is not None:
                    ax.clear()
            # plot data
            for key, value in data.items():
                ax = axs[plot_pos.get(key, (0, 0, 0))]
                args = {'label': key} | plot_args.get(key, {})
                ax.plot(*zip(*value), **args)
            # update legend
            for ax in axs.flatten():
                if ax is not None and len(ax.get_legend_handles_labels()[1]) > 0:
                    ax.legend()
                    
            return fig


        super().__init__(
            update_period=update_period,
            threaded=threaded,
            plot_init_fn=default_plot_init_fn,
            plot_update_fn=default_plot_update_fn
        )
