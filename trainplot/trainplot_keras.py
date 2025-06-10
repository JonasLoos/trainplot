from typing import Literal
from . import TrainPlot


def TrainPlotKerasCallback(frequency: Literal["epoch", "batch"] = "epoch", **trainplot_kwargs):
    '''TrainPlot callback for tensorflow/keras.

    Args:
        frequency: How often to update the plot. Either "epoch" or "batch".
        **trainplot_kwargs: Passed to `TrainPlot` constructor.

    Returns:
        A keras Callback instance.
    '''
    from keras.callbacks import Callback

    class _TrainPlotKerasCallback(Callback):
        def __init__(self):
            super().__init__()
            self.frequency = frequency

            # create trainplot with simplified arguments
            self.trainplot = TrainPlot(**trainplot_kwargs)

        def on_train_batch_end(self, batch: int, logs: dict[str, float]):
            if self.frequency == "batch":
                self.trainplot(**logs)

        def on_epoch_end(self, epoch: int, logs: dict[str, float]):
            if self.frequency == "epoch":
                self.trainplot(step=epoch, **logs)

        def on_train_end(self, logs=None):
            self.trainplot.close()

    return _TrainPlotKerasCallback()
