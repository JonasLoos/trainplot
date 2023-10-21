from typing import Literal
import keras
from . import TrainPlot


class TrainPlotKerasCallback(keras.callbacks.Callback):
    def __init__(self, frequency: Literal["epoch", "batch"] = "epoch", **trainplot_kwargs):
        '''TrainPlot callback for tensorflow/keras.

        Args:
            frequency: How often to update the plot. Either "epoch" or "batch".
            **trainplot_kwargs: Passed to `TrainPlot` constructor.
        '''
        super().__init__()

        # check arguments
        if frequency not in ["epoch", "batch"]:
            raise ValueError(f"frequency must be 'epoch' or 'batch', got {frequency}")
        self.frequency = frequency

        # setup default properties
        trainplot_kwargs = {
            'threaded': False,
            'plot_pos': {'loss': (0,0,0), 'val_loss': (0,0,0), 'accuracy': (0,0,1), 'val_accuracy': (0,0,1)},
            'plot_args': {
                'loss': {'color': 'orange', 'alpha': 0.7, 'label': 'Loss'},
                'val_loss': {'color': 'red', 'alpha': 0.7, 'label': 'Validation Loss'},
                'accuracy': {'color': 'blue', 'alpha': 0.7, 'label': 'Accuracy'},
                'val_accuracy': {'color': 'darkblue', 'alpha': 0.7, 'label': 'Validation Accuracy'},
            },
            'axis_custumization': {
                (0,0,0): lambda ax: ax.set_ylabel('Loss') and ax.set_xlabel(frequency.capitalize()),
                (0,0,1): lambda ax: ax.set_ylabel('Accuracy'),
            },
        } | trainplot_kwargs

        # create trainplot
        self.trainplot = TrainPlot(**trainplot_kwargs)

    def on_train_batch_end(self, batch: int, logs: dict[str, float]):
        if self.frequency == "batch":
            self.trainplot(**logs)

    def on_epoch_end(self, epoch: int, logs: dict[str, float]):
        if self.frequency == "epoch":
            self.trainplot(step=epoch, **logs)

    def on_train_end(self, logs=None):
        self.trainplot.close()
