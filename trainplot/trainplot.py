from typing import Any, Callable
import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import Output, Layout
from IPython.display import display
from IPython import get_ipython
import time
import threading
from collections import defaultdict



class TrainPlotBase():
    def __init__(self, update_period: float, threaded: bool, plot_init_fn: Callable[[], tuple[plt.Figure, Any]], plot_update_fn: Callable[[plt.Figure, Any, np.ndarray], plt.Figure]):
        '''
        Args:
            update_period: minimum time in seconds between plot updates.
            threaded: if `True`, plot in a separate thread (cann mess up output). If `False`, plot in the main thread (slower).
                If you experience problems with other output vanishing or ending up in the plot, try setting this to `False`.
            plot_init_fn: function that creates the plot.
            plot_update_fn: function that updates the plot.
        '''
        # check arguments
        if update_period < 0:
            raise ValueError(f'update_period must be positive, got {update_period}')

        # setup properties
        self.plot_update_fn = plot_update_fn
        self.update_period = update_period
        self.new_data = False  # signals to the plotting thread that new data is available
        self.data = dict()
        self.update_step = 0
        self.threaded = threaded
        self.plot_thread = None  # thread that periodically updates the plot
        self.stop_thread = False  # signals to the plotting thread that it should stop
        self.last_update = 0  # time.time() of last plot update

        # setup output widget
        self.fig, self.init_results = plot_init_fn()
        # TODO: move this to e.g. plot_init_fn, cuz I want to keep TrainPlotBase independent from matplotlib
        fig_height = f'{self.fig.get_size_inches()[1]*1.04-0.04}in' if isinstance(self.fig, plt.Figure) else None  # fix/limit size of output widget, to prevent flickering
        self.out = Output(layout=Layout(height=fig_height, overflow='hidden'))
        display(self.out)
        self.update_plot()
        plt.close(self.fig)

    def update_plot(self):
        self.out.clear_output(wait=True)
        self.out.append_display_data(self.plot_update_fn(self.fig, self.init_results, self.data))
        self.out.outputs = self.out.outputs[-1:]

    def _update_plot_periodically(self):
        '''Update the plot periodically. This function is made to be called in a separate thread.'''
        # plot as long as new data is coming in faster than the update period
        while self.new_data:
            self.new_data = False  # possible race condition (could cause plotting of even newer data than expected - not a problem)
            self.last_update = time.time()
            # plot all data
            self.update_plot()
            # wait for next update, while checking if the thread should stop
            while time.time() - self.last_update < self.update_period:
                if self.stop_thread:
                    return  # exit thread
                time.sleep(0.05)

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
            self.new_data = True
            # start plotting thread if not already running
            if self.plot_thread is None or not self.plot_thread.is_alive():
                self.plot_thread = threading.Thread(target=self._update_plot_periodically)  # possible race condition (could spawn multiple threads)
                self.plot_thread.start()
        else:
            # plot in main thread if enough time has passed since the last plot
            if time.time() - self.last_update > self.update_period:
                self.last_update = time.time()
                self.update_plot()

        # mark this TrainPlot object as active
        global currently_active_trainplot_objects
        currently_active_trainplot_objects.add(self)

    def __call__(self, **args):
        '''Shutcut for `update` function.'''
        self.update(**args)

    def close(self):
        '''Do a final plot update.'''
        if self.threaded:
            # prevent waiting, by setting stop_thread to True, which causes the thread to exit immediately
            self.stop_thread = True
            if self.plot_thread is not None:
                self.plot_thread.join()
        # final update
        self.update_plot()




class TrainPlot(TrainPlotBase):
    def __init__(self, update_period: float = 0.5, threaded: bool = False, fig_args: dict[str, Any] = {}, plot_pos: dict[str, tuple[int,int,int]] = {}, plot_args: dict[str,dict[str,Any]] = {}, axis_custumization: dict[tuple[int,int,int], Callable[[plt.Axes], None]] = {}):
        '''
        Args:
            update_period: minimum time in seconds between updates. 
                Setting this to a low value (< 0.5) can significantly slow down training.
            threaded: if `True`, plot in a separate thread (faster). If `False`, plot in the main thread (slower).
                If you experience problems with other output vanishing or ending up in the plot, try setting this to `False`.
            fig_args: arguments passed to `plt.subplots`.
            plot_pos: dictionary mapping data keys to plot positions.
                plot_pos[key] = (row, column, twinx)
                    row: row index of plot
                    column: column index of plot
                    twinx: if 1, plot on secondary y-axis
            plot_args: arguments passed to `plt.plot`.
            axis_custumization: dictionary mapping plot positions to functions that customize the axis.
        
        Examples:
        ```
        # default
        trainplot = TrainPlot()
        # custom with twinx
        trainplot = TrainPlot(
            update_period=2,
            fig_args={'figsize': (10, 8)},
            plot_pos={'loss': (0, 0, 0), 'accuracy': (0, 0, 1)},
            plot_args={'loss': {'color': 'red'}, 'accuracy': {'color': 'blue'}}
        )
        # custom with 4 axes
        trainplot = TrainPlot(
            fig_args=dict(
                nrows=2,
                ncols=2,
                figsize=(10, 10),
                gridspec_kw={'height_ratios': [1, 2], 'width_ratios': [1, 1]}
            ),
            plot_pos={
                'loss': (0, 0, 0), 'accuracy': (0, 1, 0),
                'val_loss': (1, 0, 0), 'val_accuracy': (1, 1, 0)
            }
        )
        ```
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
            for pos in plot_pos.values():
                if pos[2] == 1 and axs[pos] is None and axs[pos[0], pos[1], 0] is not None:
                    axs[pos] = axs[pos[0], pos[1], 0].twinx()
            # custom axis custumization
            for pos, func in axis_custumization.items():
                func(axs[pos])
            fig.tight_layout()
            return fig, axs

        def default_plot_update_fn(fig, axs, data: np.ndarray):
            # clear axes
            for ax in axs.flatten():
                if ax is not None:
                    # clear lines, so they can be redrawn
                    for line in ax.get_lines():
                        line.remove()
                    # reset color cycle, so that the colors don't change
                    ax.set_prop_cycle(None)
            # plot data
            for key, value in data.items():
                ax = axs[plot_pos.get(key, (0, 0, 0))]
                args = {'label': key} | plot_args.get(key, {})
                ax.plot(*zip(*value), **args)
            # update legend
            for axs_row in axs:
                for ax in axs_row:
                    ax1, ax2 = ax
                    lines = []
                    if ax1 is not None:
                        lines += ax1.get_lines()
                    if ax2 is not None:
                        lines += ax2.get_lines()
                    if len(lines) > 0:
                        if ax1 is not None:
                            ax1.legend(handles=lines)
                        else:
                            ax2.legend(handles=lines)
            # return figure to be displayed
            return fig

        # call super constructor with default plot functions
        super().__init__(
            update_period=update_period,
            threaded=threaded,
            plot_init_fn=default_plot_init_fn,
            plot_update_fn=default_plot_update_fn
        )


def plot(**args):
    '''Create or update an unnamed TrainPlot object for the current cell.

    Compared to a TrainPlot object, this function doesn't need initialization.
    However, therefore, no customizations are possible.

    Args:
        NAME=NEW_VALUE, ...: Where NAME is the name of the data to update and NEW_VALUE is the new value to append to the data list.

    Examples:
    ```python
    for i in range(5):
        plot(i=i)
    ```
    '''
    global unnamed_trainplot_objects
    # get current TrainPlot object
    i = ipython_instance.execution_count
    if i not in unnamed_trainplot_objects:
        unnamed_trainplot_objects[i] = TrainPlot()
    # update TrainPlot object
    unnamed_trainplot_objects[i].update(**args)



def close_ipython_cell(*args, **kwargs):
    '''This closes all TrainPlot objects that were updated in the current cell. This makes sure all data is plotted before the cell is finished.'''
    global currently_active_trainplot_objects
    for tp in currently_active_trainplot_objects:
        tp.close()
    currently_active_trainplot_objects.clear()



ipython_instance = get_ipython()
ipython_instance.events.register('post_run_cell', close_ipython_cell)

currently_active_trainplot_objects: set[TrainPlotBase] = set()
unnamed_trainplot_objects = defaultdict(lambda: TrainPlot)
