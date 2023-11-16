from ._version import __version__, __version_tuple__

from .trainplot import TrainPlot, plot

def TrainPlotKeras(*args, **kwargs):
    """TrainPlot callback for Keras.
    Args:
        **kwargs: key-arguments which are passed to TrainPlot

    Notes:
        Requires keras to be installed.
    """
    # This function is defined here to only require keras when TrainPlotKeras is used.
    from .trainplot_keras import TrainPlotKerasCallback
    return TrainPlotKerasCallback(*args, **kwargs)
