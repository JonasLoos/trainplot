from typing import Literal
import keras
from . import TrainPlot


class TrainPlotKerasCallback(keras.callbacks.Callback):
    def __init__(self, frequency: Literal["epoch", "batch"] = "batch"):
        super().__init__()
        self.trainplot = TrainPlot(threaded=False)
        self.frequency = frequency

    def on_train_batch_end(self, batch: int, logs: dict[str, float]):
        if self.frequency == "batch":
            self.trainplot(**logs)

    def on_epoch_end(self, epoch: int, logs: dict[str, float]):
        if self.frequency == "epoch":
            self.trainplot(**logs)

    def on_train_end(self, logs=None):
        self.trainplot.close()
