"""
Minimal train-plot library for Jupyter notebooks.
A simple plotting library for monitoring training progress.
"""

import time
import uuid
import json
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from IPython.display import display, Javascript
from IPython import get_ipython


class TrainPlotFigure:
    """A custom figure class for training plots that renders using HTML5 Canvas."""

    def __init__(self, width: int = 600, height: int = 400):
        """Create a figure for training plots."""
        self.width = width
        self.height = height
        self.data: Dict[str, List[Tuple[float, float]]] = {}

        # Generate unique identifiers for this figure
        js_id = uuid.uuid4().hex[:8]
        self._js_figure_id = f"trainplot_figure_{js_id}"
        self._js_func_name = f"renderTrainPlot_{js_id}"

    def update_data(self, data: Dict[str, List[Tuple[float, float]]]):
        """Update the figure with new data."""
        self.data = data.copy()

    def update_display(self):
        """Update the display in Jupyter notebook."""
        update_js = f"""
        (function() {{
            const data = {json.dumps(self.data)};
            const el = document.getElementById('{self._js_figure_id}');
            if (!el) return;
            const canvas = el.querySelector('canvas');
            if (!canvas) return;
            window.{self._js_func_name}(canvas, data);
        }})();
        """
        display(Javascript(update_js))

    def _get_render_js(self):
        """Get the complete JavaScript code for rendering."""
        return f"""
        function {self._js_func_name}(canvas, data) {{
            const ctx = canvas.getContext("2d");
            const w = canvas.width = {self.width};
            const h = canvas.height = {self.height};
            const padding = 60;
            const plotWidth = w - 2 * padding;
            const plotHeight = h - 2 * padding;

            // Clear canvas
            ctx.fillStyle = "#ffffff";
            ctx.fillRect(0, 0, w, h);
            ctx.strokeStyle = "#e0e0e0";
            ctx.lineWidth = 1;
            ctx.strokeRect(padding, padding, plotWidth, plotHeight);

            // Exit early if no data
            if (!data || Object.keys(data).length === 0) {{
                ctx.fillStyle = "#666";
                ctx.font = "14px Arial";
                ctx.textAlign = "center";
                ctx.fillText("No data", w/2, h/2);
                return;
            }}

            // Calculate global bounds
            let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
            Object.values(data).forEach(series => {{
                series.forEach(([x, y]) => {{
                    xmin = Math.min(xmin, x);
                    xmax = Math.max(xmax, x);
                    ymin = Math.min(ymin, y);
                    ymax = Math.max(ymax, y);
                }});
            }});

            // Add padding to ranges
            const xrange = xmax - xmin || 1;
            const yrange = ymax - ymin || 1;
            xmin -= xrange * 0.05;
            xmax += xrange * 0.05;
            ymin -= yrange * 0.05;
            ymax += yrange * 0.05;

            // Helper function to convert data coordinates to pixel coordinates
            const toPixel = (x, y) => [
                padding + (x - xmin) / (xmax - xmin) * plotWidth,
                padding + plotHeight - (y - ymin) / (ymax - ymin) * plotHeight
            ];

            // Color palette
            const colors = [
                "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
            ];

            // Draw grid
            ctx.strokeStyle = "#f0f0f0";
            ctx.lineWidth = 1;
            for (let i = 1; i < 5; i++) {{
                const x = padding + (i / 5) * plotWidth;
                const y = padding + (i / 5) * plotHeight;
                ctx.beginPath();
                ctx.moveTo(x, padding);
                ctx.lineTo(x, padding + plotHeight);
                ctx.moveTo(padding, y);
                ctx.lineTo(padding + plotWidth, y);
                ctx.stroke();
            }}

            // Draw data series
            Object.entries(data).forEach(([name, series], index) => {{
                if (series.length === 0) return;
                const color = colors[index % colors.length];
                ctx.strokeStyle = color;
                ctx.fillStyle = color;
                ctx.lineWidth = 2;

                // Draw line
                ctx.beginPath();
                series.forEach(([x, y], i) => {{
                    const [px, py] = toPixel(x, y);
                    if (i === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                }});
                ctx.stroke();

                // Draw points
                series.forEach(([x, y]) => {{
                    const [px, py] = toPixel(x, y);
                    ctx.beginPath();
                    ctx.arc(px, py, 3, 0, 2 * Math.PI);
                    ctx.fill();
                }});
            }});

            // Draw axes labels
            ctx.fillStyle = "#333";
            ctx.font = "12px Arial";
            ctx.textAlign = "center";
            for (let i = 0; i <= 5; i++) {{
                const x = padding + (i / 5) * plotWidth;
                const value = xmin + (i / 5) * (xmax - xmin);
                ctx.fillText(value.toFixed(1), x, h - 10);
            }}
            ctx.textAlign = "right";
            for (let i = 0; i <= 5; i++) {{
                const y = padding + plotHeight - (i / 5) * plotHeight;
                const value = ymin + (i / 5) * (ymax - ymin);
                ctx.fillText(value.toFixed(2), padding - 10, y + 4);
            }}

            // Draw legend
            ctx.textAlign = "left";
            ctx.font = "12px Arial";
            let legendY = padding + 20;
            Object.entries(data).forEach(([name, _], index) => {{
                const color = colors[index % colors.length];
                ctx.fillStyle = color;
                ctx.fillRect(w - 150, legendY - 8, 12, 12);
                ctx.fillStyle = "#333";
                ctx.fillText(name, w - 130, legendY);
                legendY += 20;
            }});
        }}
        window.{self._js_func_name} = {self._js_func_name};
        """

    def _repr_mimebundle_(self, include=None, exclude=None):
        """Return MIME bundle for Jupyter display protocol."""
        html_content = f"""
        <div id="{self._js_figure_id}" style="width: {self.width}px; height: {self.height}px; border: 1px solid #ddd; border-radius: 4px; overflow: hidden;"></div>
        <script>
        {self._get_render_js()}
        (function() {{
            const data = {json.dumps(self.data)};
            const el = document.getElementById('{self._js_figure_id}');
            if (!el) return;
            const canvas = document.createElement("canvas");
            canvas.style.display = "block";
            el.appendChild(canvas);
            {self._js_func_name}(canvas, data);
        }})();
        </script>
        """
        data_summary = f"{len(self.data)} series" if self.data else "no data"
        return {
            "text/html": html_content,
            "text/plain": f"<TrainPlotFigure with {data_summary}>"
        }


class TrainPlot:
    """Main TrainPlot class for monitoring training progress."""

    def __init__(self, update_period: float = 0.1, width: int = 600, height: int = 400):
        """Create a TrainPlot instance."""
        if update_period < 0:
            raise ValueError(f'update_period must be positive, got {update_period}')

        self.update_period = update_period
        self.data: Dict[str, List[Tuple[float, float]]] = {}
        self.update_step = 0
        self.last_update = 0
        self.figure = TrainPlotFigure(width, height)

        if ENV.ipython_instance is not None:
            display(self.figure)

    def update(self, **kwargs):
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
        update_step = self.update_step
        for key, value in kwargs.items():
            if key == 'step':
                update_step = value
            elif key == 'epoch':
                raise NotImplementedError('Epochs not supported yet')
            elif key not in self.data:
                self.data[key] = [(update_step, value)]
            else:
                self.data[key].append((update_step, value))
        self.update_step += 1

        if time.time() - self.last_update > self.update_period:
            self.last_update = time.time()
            self.update_plot()

        ENV.currently_active_trainplot_objects.add(self)

    def update_plot(self):
        """Update the plot with the current data."""
        if ENV.ipython_instance is not None:
            self.figure.update_data(self.data)
            self.figure.update_display()

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
