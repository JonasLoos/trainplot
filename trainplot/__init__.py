from ._version import __version__, __version_tuple__

from .trainplot import TrainPlot

def TrainPlotKeras(*args, **kwargs):
    """TrainPlot callback for Keras.
    Args:
        **kwargs: key-arguments which are passed to TrainPlot

    Notes:
        Requires keras to be installed.
    """
    from .trainplot_keras import TrainPlotKerasCallback
    return TrainPlotKerasCallback(*args, **kwargs)
