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
    def __init__(self, update_period: float = 0.5, threaded: bool = False):
        '''
        Args:
            update_period: minimum time in seconds between plot updates.
            threaded: if `True`, plot in a separate thread (cann mess up output). If `False`, plot in the main thread (slower).
                If you experience problems with other output vanishing or ending up in the plot, try setting this to `False`.
        '''
        # check arguments
        if update_period < 0:
            raise ValueError(f'update_period must be positive, got {update_period}')

        # setup properties
        self.update_period = update_period
        self.new_data = False  # signals to the plotting thread that new data is available
        self.data = dict()
        self.update_step = 0
        self.threaded = threaded
        self.plot_thread = None  # thread that periodically updates the plot
        self.stop_thread = False  # signals to the plotting thread that it should stop
        self.last_update = 0  # time.time() of last plot update

        self.init_plot()
        self.update_plot()

    def init_plot(self):
        '''Create the plot.'''
        raise NotImplementedError('init_plot must be implemented by subclass')

    def update_plot(self):
        '''Update the plot with the current data.'''
        raise NotImplementedError('update_plot must be implemented by subclass')

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



class TrainPlotOutputWidget(TrainPlotBase):
    '''A wrapper around TrainPlotBase that displays the plot in an output widget.'''
    def __init__(self, *args, plot_init_fn: Callable[[], tuple[Any, dict]], plot_update_fn: Callable[[Any, np.ndarray], Any], **kwargs):
        self.plot_init_fn = plot_init_fn
        self.plot_update_fn = plot_update_fn
        super().__init__(*args, **kwargs)
    
    def init_plot(self):
        '''Create the plot.'''
        # setup output widget, if running in IPython
        if ipython_instance is not None:
            self.figure_data, layout_args = self.plot_init_fn()
            self.out = Output(layout=Layout(**layout_args))
            display(self.out)
        else:
            self.figure_data = None
            self.out = None

    def update_plot(self):
        '''Update the plot with the current data.'''
        if self.out is None:
            return
        self.out.clear_output(wait=True)
        self.out.append_display_data(self.plot_update_fn(self.figure_data, self.data))
        self.out.outputs = self.out.outputs[-1:]



class TrainPlotMpl(TrainPlotOutputWidget):
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
            plt.close(fig)  # close figure, to prevent jupyter from displaying it a second time
            fig_height = f'{fig.get_size_inches()[1]*1.04-0.04}in'  # fix/limit size of output widget, to prevent flickering
            layout_args = dict(height=fig_height, overflow='hidden')
            return (fig, axs), layout_args

        def default_plot_update_fn(figure_data, data: np.ndarray):
            fig, axs = figure_data
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
        
        super().__init__(
            update_period=update_period,
            threaded=threaded,
            plot_init_fn=default_plot_init_fn,
            plot_update_fn=default_plot_update_fn
        )



class TrainPlotPlotly(TrainPlotBase):
    '''Plot using plotly.'''
    def __init__(self, update_period: float = 0.5, threaded: bool = False, fig_args: dict[str, Any] = {}, plot_pos: dict[str, tuple[int,int,int]] = {}, plot_args: dict[str, dict[str,Any]] = {}):
        '''
        Args:
            update_period: minimum time in seconds between updates. 
                Setting this to a low value (< 0.5) can significantly slow down training.
            threaded: if `True`, plot in a separate thread (faster). If `False`, plot in the main thread (slower).
                If you experience problems with other output vanishing or ending up in the plot, try setting this to `False`.
            fig_args: arguments passed to `go.FigureWidget`. Default: `{'layout': {'height': 450}}`.
            plot_pos: dictionary mapping data keys to plot positions.
                plot_pos[key] = (row, column, twinx)
                    row: row index of plot
                    column: column index of plot
                    secondary y-axis: if 1, plot on secondary y-axis
            plot_args: arguments passed to `fig.add_trace` (by default `go.Scatter`).

        Examples:
        ```
        tp = TrainPlotPlotly(
            update_period=0.2,
            fig_args={'layout': {'title': 'My Train Plot', 'height': 600}},
            plot_pos={'acc': (0, 0, 0), 'loss': (0, 0, 1), 'val_acc': (0, 0, 0), 'val_loss': (0, 0, 1), 'stuff': (1, 0, 0)},
            plot_args={'acc': {'name': 'accuracy', 'line': {'color':'gold'}}, 'stuff': {'type': 'bar'}})
        tp.fig.update_yaxes(row=2, col=1, type="log")  # log scale
        ...
        tp(acc=50, val_acc=40, loss=0.5, val_loss=0.5, stuff=42)
        tp(acc=70, val_acc=50, loss=0.3, val_loss=0.35, stuff=420)
        ```
        '''
        self.fig_args = fig_args
        self.plot_pos = plot_pos
        self.plot_args = plot_args
        super().__init__(update_period=update_period, threaded=threaded)

    def init_plot(self):
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        rows = max([0] + [x[0] for x in self.plot_pos.values()]) + 1
        cols = max([0] + [x[1] for x in self.plot_pos.values()]) + 1
        self.fig = go.FigureWidget(make_subplots(
            rows=rows,
            cols=cols,
            specs = [[{"secondary_y": True}]*cols]*rows,
            figure = go.Figure(**self.fig_args),
        ))
        display(self.fig)
    
    def update_plot(self):
        import plotly.graph_objects as go
        traces = {trace.name: trace for trace in self.fig.data}
        for key, value in self.data.items():
            name = self.plot_args.get(key, {}).get('name', key)
            if name in traces:
                # update existing trace
                traces[name].x = [x for x, _ in value]
                traces[name].y = [y for _, y in value]
            else:
                # add new trace
                row, col, secy = self.plot_pos.get(key, (0,0,0))
                self.fig.add_trace(
                    dict(
                        x = [x for x, _ in value],
                        y = [y for _, y in value],
                        **({'name': key} | self.plot_args.get(key, {}))
                    ),
                    row=row+1,
                    col=col+1,
                    secondary_y=secy
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
    # check if running in IPython and do nothing if not
    if ipython_instance is None:
        return

    # update TrainPlot object for current cell
    global unnamed_trainplot_objects
    unnamed_trainplot_objects[ipython_instance.execution_count].update(**args)



def close_ipython_cell(*args, **kwargs):
    '''This closes all TrainPlot objects that were updated in the current cell. This makes sure all data is plotted before the cell is finished.'''
    global currently_active_trainplot_objects
    for tp in currently_active_trainplot_objects:
        tp.close()
    currently_active_trainplot_objects.clear()


# setup ipython hooks
ipython_instance = get_ipython()
if ipython_instance is not None:
    ipython_instance.events.register('post_run_cell', close_ipython_cell)
else:
    print('WARNING: It seems you are running trainplot outside of an IPython environment. No plots will be displayed.')


# global variables
currently_active_trainplot_objects: set[TrainPlotBase] = set()
unnamed_trainplot_objects = defaultdict(TrainPlotPlotly)
