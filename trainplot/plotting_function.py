js_code = """
function render({ model, el }) {
    // Create canvas element
    const canvas = document.createElement("canvas");
    canvas.style.display = "block";
    canvas.style.border = "1px solid #ddd";
    canvas.style.borderRadius = "4px";
    el.appendChild(canvas);

    // Plotting function
    function renderPlot() {
        const data = model.get("data");
        const reduction_factor = model.get("reduction_factor");
        const max_step = model.get("max_step");
        const w = canvas.width = model.get("width");
        const h = canvas.height = model.get("height");

        const ctx = canvas.getContext("2d");
        const padding_left = 60;
        const padding_top = 20;
        const padding_right = 20;
        const padding_bottom = 40;
        const plotWidth = w - padding_left - padding_right;
        const plotHeight = h - padding_top - padding_bottom;

        // Clear canvas
        ctx.fillStyle = "#ffffff";
        ctx.fillRect(0, 0, w, h);
        ctx.strokeStyle = "#e0e0e0";
        ctx.lineWidth = 1;
        ctx.strokeRect(padding_left, padding_top, plotWidth, plotHeight);

        // Exit early if no data
        if (!data || Object.keys(data).length === 0) {
            ctx.fillStyle = "#666";
            ctx.font = "14px Arial";
            ctx.textAlign = "center";
            ctx.fillText("No data", w/2, h/2);
            return;
        }

        // Calculate global bounds
        let xmin = 0, xmax = max_step/reduction_factor, ymin = Infinity, ymax = -Infinity;
        Object.values(data).forEach(series => {
            xmax = Math.max(xmax, series.length - 1);
            series.forEach(y => {
                if (!isNaN(y)) {
                    ymin = Math.min(ymin, y);
                    ymax = Math.max(ymax, y);
                }
            });
        });

        // Handle case where all values are NaN
        if (ymin === Infinity) {
            ymin = ymax = 0;
        }

        // Add padding to ranges
        const xrange = xmax - xmin || 1;
        const yrange = ymax - ymin || 1;
        xmin -= xrange * 0.05;
        xmax += xrange * 0.05;
        ymin -= yrange * 0.05;
        ymax += yrange * 0.05;

        // Helper function to find nice tick values
        const getNiceTicks = (min, max, targetCount = 5) => {
            const range = max - min;
            if (range === 0) return [min];

            const roughStep = range / targetCount;
            const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
            const normalized = roughStep / magnitude;
            let niceStep;
            if (normalized <= 1) niceStep = magnitude;
            else if (normalized <= 2) niceStep = 2 * magnitude;
            else if (normalized <= 5) niceStep = 5 * magnitude;
            else niceStep = 10 * magnitude;

            const startTick = Math.ceil(min / niceStep) * niceStep;
            const ticks = [];
            for (let tick = startTick; tick <= max; tick += niceStep) {
                const roundedTick = Math.round(tick / niceStep) * niceStep;
                if (roundedTick >= min && roundedTick <= max) {
                    ticks.push(roundedTick);
                }
            }
            return ticks.length > 0 ? ticks : [min, max];
        };

        // Helper function to convert data coordinates to pixel coordinates
        const toPixel = (x, y) => [
            padding_left + (x - xmin) / (xmax - xmin) * plotWidth,
            padding_top + plotHeight - (y - ymin) / (ymax - ymin) * plotHeight
        ];

        // Get nice tick values
        const xTicks = getNiceTicks(xmin*reduction_factor, xmax*reduction_factor);
        const yTicks = getNiceTicks(ymin, ymax);

        // Color palette
        const colors = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
            "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
        ];

        // Draw grid
        ctx.strokeStyle = "#f0f0f0";
        ctx.lineWidth = 1;

        // Vertical grid lines
        xTicks.forEach(tickValue => {
            const [px, _] = toPixel(tickValue/reduction_factor, 0);
            ctx.beginPath();
            ctx.moveTo(px, padding_top);
            ctx.lineTo(px, padding_top + plotHeight);
            ctx.stroke();
        });

        // Horizontal grid lines
        yTicks.forEach(tickValue => {
            const [_, py] = toPixel(0, tickValue);
            ctx.beginPath();
            ctx.moveTo(padding_left, py);
            ctx.lineTo(padding_left + plotWidth, py);
            ctx.stroke();
        });

        // Draw data series
        Object.entries(data).forEach(([name, series], index) => {
            if (series.length === 0) return;
            const color = colors[index % colors.length];
            ctx.strokeStyle = color;
            ctx.fillStyle = color;
            ctx.lineWidth = 2;

            // Draw line (skip NaN values)
            ctx.beginPath();
            let isFirstPoint = true;
            series.forEach((y, i) => {
                if (!isNaN(y)) {
                    const [px, py] = toPixel(i, y);
                    if (isFirstPoint) {
                        ctx.moveTo(px, py);
                        isFirstPoint = false;
                    } else {
                        ctx.lineTo(px, py);
                    }
                }
            });
            ctx.stroke();

            // Draw points (skip NaN values)
            series.forEach((y, i) => {
                if (!isNaN(y)) {
                    const [px, py] = toPixel(i, y);
                    ctx.beginPath();
                    ctx.arc(px, py, 3, 0, 2 * Math.PI);
                    ctx.fill();
                }
            });
        });

        // Draw axes labels
        ctx.fillStyle = "#333";
        ctx.font = "12px Arial";

        // X-axis labels
        ctx.textAlign = "center";
        xTicks.forEach(tickValue => {
            const [px, _] = toPixel(tickValue/reduction_factor, 0);
            const label = tickValue === 0 ? "0" :
                            Math.abs(tickValue) < 0.01 ? tickValue.toExponential(1) :
                            tickValue % 1 === 0 ? tickValue.toString() :
                            tickValue.toFixed(2);
            ctx.fillText(label, px, h - 10);
        });

        // Y-axis labels
        ctx.textAlign = "right";
        yTicks.forEach(tickValue => {
            const [_, py] = toPixel(0, tickValue);
            const label = tickValue === 0 ? "0" :
                            Math.abs(tickValue) < 0.01 ? tickValue.toExponential(1) :
                            tickValue % 1 === 0 ? tickValue.toString() :
                            tickValue.toFixed(2);
            ctx.fillText(label, padding_left - 10, py + 4);
        });

        // Draw legend
        if (Object.keys(data).length > 0) {
            ctx.textAlign = "left";
            ctx.font = "12px Arial";
            ctx.fillStyle = "rgba(255, 255, 255, 0.9)";
            ctx.fillRect(w - 155, padding_top, 155, Object.keys(data).length * 18 + 10);
            let legendY = padding_top + 18;
            Object.entries(data).forEach(([name, _], index) => {
                const color = colors[index % colors.length];
                ctx.fillStyle = color;
                ctx.fillRect(w - 150, legendY - 10, 10, 10);
                ctx.fillStyle = "#333";
                ctx.fillText(name, w - 135, legendY);
                legendY += 18;
            });
        }

        // Store data for hover functionality
        canvas.plotData = data;
        canvas.toPixel = toPixel;
        canvas.colors = colors;
        canvas.padding = { left: padding_left, top: padding_top, right: padding_right, bottom: padding_bottom };
        canvas.plotBounds = { xmin, xmax, ymin, ymax };
    }

    // Mouse hover functionality
    const findNearestPoint = (mouseX, mouseY) => {
        const data = canvas.plotData;
        if (!data) return null;

        let nearestPoint = null;
        let minDistance = Infinity;
        let nearestSeries = null;

        Object.entries(data).forEach(([seriesName, series]) => {
            series.forEach((y, i) => {
                if (!isNaN(y)) {
                    const [px, py] = canvas.toPixel(i, y);
                    const distance = Math.sqrt((mouseX - px) ** 2 + (mouseY - py) ** 2);
                    if (distance < minDistance && distance < 20) {
                        minDistance = distance;
                        nearestPoint = [i, y];
                        nearestSeries = seriesName;
                    }
                }
            });
        });

        return nearestPoint ? { point: nearestPoint, series: nearestSeries, distance: minDistance } : null;
    };

    const drawTooltip = (mouseX, mouseY, pointInfo) => {
        if (!pointInfo) return;

        const ctx = canvas.getContext("2d");
        const [x, y] = pointInfo.point;
        const seriesName = pointInfo.series;
        const reduction_factor = model.get("reduction_factor");

        const xTick = x * reduction_factor;
        const xLabel = xTick % 1 === 0 ? xTick.toString() : xTick.toFixed(3);
        const yLabel = y % 1 === 0 ? y.toString() : y.toFixed(3);
        const text = `${seriesName}: (${xLabel}, ${yLabel})`;

        ctx.font = "12px Arial";
        const textWidth = ctx.measureText(text).width;
        const tooltipWidth = textWidth + 12;
        const tooltipHeight = 24;

        let tooltipX = mouseX + 10;
        let tooltipY = mouseY - 10;

        if (tooltipX + tooltipWidth > canvas.width) tooltipX = mouseX - tooltipWidth - 10;
        if (tooltipY - tooltipHeight < 0) tooltipY = mouseY + tooltipHeight + 10;

        ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
        ctx.fillRect(tooltipX, tooltipY - tooltipHeight, tooltipWidth, tooltipHeight);

        ctx.fillStyle = "#fff";
        ctx.textAlign = "left";
        ctx.fillText(text, tooltipX + 6, tooltipY - 8);

        const [px, py] = canvas.toPixel(x, y);
        const seriesIndex = Object.keys(canvas.plotData).indexOf(seriesName);
        const color = canvas.colors[seriesIndex % canvas.colors.length];

        ctx.strokeStyle = "#fff";
        ctx.fillStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
    };

    const handleMouseMove = (event) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;

        renderPlot();

        if (mouseX >= canvas.padding.left && mouseX <= canvas.width - canvas.padding.right &&
            mouseY >= canvas.padding.top && mouseY <= canvas.height - canvas.padding.bottom) {
            const nearestPoint = findNearestPoint(mouseX, mouseY);
            if (nearestPoint) {
                drawTooltip(mouseX, mouseY, nearestPoint);
            }
        }
    };

    const handleMouseLeave = () => {
        renderPlot();
    };

    // Set up event listeners
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    // Initial render
    renderPlot();

    // Listen for data changes from Python
    // use a custom message instead of event listeners on data change so that 
    // we only have one render per update, not one per changed variable
    model.on("msg:custom", msg => {
        if (msg?.render) {renderPlot()}
    })
}

export default { render };
"""
