js_code = """
function FUNC_NAME(canvas, data) {
    const ctx = canvas.getContext("2d");
    const w = canvas.width = WIDTH;
    const h = canvas.height = HEIGHT;
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
    let xmin = Infinity, xmax = -Infinity, ymin = Infinity, ymax = -Infinity;
    Object.values(data).forEach(series => {
        series.forEach(([x, y]) => {
            xmin = Math.min(xmin, x);
            xmax = Math.max(xmax, x);
            ymin = Math.min(ymin, y);
            ymax = Math.max(ymax, y);
        });
    });

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
        
        // Calculate rough step size
        const roughStep = range / targetCount;
        
        // Find the magnitude (power of 10)
        const magnitude = Math.pow(10, Math.floor(Math.log10(roughStep)));
        
        // Find nice step size (1, 2, or 5 times the magnitude)
        const normalized = roughStep / magnitude;
        let niceStep;
        if (normalized <= 1) niceStep = magnitude;
        else if (normalized <= 2) niceStep = 2 * magnitude;
        else if (normalized <= 5) niceStep = 5 * magnitude;
        else niceStep = 10 * magnitude;
        
        // Find starting tick (first multiple of niceStep >= min)
        const startTick = Math.ceil(min / niceStep) * niceStep;
        
        // Generate ticks
        const ticks = [];
        for (let tick = startTick; tick <= max; tick += niceStep) {
            // Handle floating point precision issues
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
    const xTicks = getNiceTicks(xmin, xmax);
    const yTicks = getNiceTicks(ymin, ymax);

    // Color palette
    const colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ];

    // Draw grid
    ctx.strokeStyle = "#f0f0f0";
    ctx.lineWidth = 1;
    
    // Vertical grid lines (x-axis ticks)
    xTicks.forEach(tickValue => {
        const [px, _] = toPixel(tickValue, 0);
        ctx.beginPath();
        ctx.moveTo(px, padding_top);
        ctx.lineTo(px, padding_top + plotHeight);
        ctx.stroke();
    });
    
    // Horizontal grid lines (y-axis ticks)
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

        // Draw line
        ctx.beginPath();
        series.forEach(([x, y], i) => {
            const [px, py] = toPixel(x, y);
            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        });
        ctx.stroke();

        // Draw points
        series.forEach(([x, y]) => {
            const [px, py] = toPixel(x, y);
            ctx.beginPath();
            ctx.arc(px, py, 3, 0, 2 * Math.PI);
            ctx.fill();
        });
    });

    // Draw axes labels
    ctx.fillStyle = "#333";
    ctx.font = "12px Arial";
    
    // X-axis labels
    ctx.textAlign = "center";
    xTicks.forEach(tickValue => {
        const [px, _] = toPixel(tickValue, 0);
        // Format number nicely
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
        // Format number nicely
        const label = tickValue === 0 ? "0" :
                     Math.abs(tickValue) < 0.01 ? tickValue.toExponential(1) : 
                     tickValue % 1 === 0 ? tickValue.toString() : 
                     tickValue.toFixed(2);
        ctx.fillText(label, padding_left - 10, py + 4);
    });

    // Draw legend
    ctx.textAlign = "left";
    ctx.font = "12px Arial";
    ctx.fillStyle = "#fff8";
    ctx.fillRect(w - 155, padding_top, 155, Object.keys(data).length * 18 + 10);  // semi-transparent background
    let legendY = padding_top + 18;
    Object.entries(data).forEach(([name, _], index) => {
        const color = colors[index % colors.length];
        ctx.fillStyle = color;
        ctx.fillRect(w - 150, legendY - 10, 10, 10);  // square
        ctx.fillStyle = "#333";
        ctx.fillText(name, w - 135, legendY);  // text
        legendY += 18;
    });

    // Store data and helper functions for hover functionality
    canvas.plotData = data;
    canvas.toPixel = toPixel;
    canvas.colors = colors;
    canvas.padding = { left: padding_left, top: padding_top, right: padding_right, bottom: padding_bottom };
    canvas.plotBounds = { xmin, xmax, ymin, ymax };

    // Helper function to find nearest point to mouse position
    const findNearestPoint = (mouseX, mouseY) => {
        let nearestPoint = null;
        let minDistance = Infinity;
        let nearestSeries = null;

        Object.entries(data).forEach(([seriesName, series]) => {
            series.forEach(([x, y]) => {
                const [px, py] = toPixel(x, y);
                const distance = Math.sqrt((mouseX - px) ** 2 + (mouseY - py) ** 2);
                if (distance < minDistance && distance < 20) { // Only consider points within 20 pixels
                    minDistance = distance;
                    nearestPoint = [x, y];
                    nearestSeries = seriesName;
                }
            });
        });

        return nearestPoint ? { point: nearestPoint, series: nearestSeries, distance: minDistance } : null;
    };

    // Helper function to draw tooltip
    const drawTooltip = (mouseX, mouseY, pointInfo) => {
        if (!pointInfo) return;

        const [x, y] = pointInfo.point;
        const seriesName = pointInfo.series;

        // Format the values
        const xLabel = x % 1 === 0 ? x.toString() : x.toFixed(3);
        const yLabel = y % 1 === 0 ? y.toString() : y.toFixed(3);
        const text = `${seriesName}: (${xLabel}, ${yLabel})`;

        // Measure text to size tooltip
        ctx.font = "12px Arial";
        const textWidth = ctx.measureText(text).width;
        const tooltipWidth = textWidth + 12;
        const tooltipHeight = 24;

        // Position tooltip (avoid going off canvas)
        let tooltipX = mouseX + 10;
        let tooltipY = mouseY - 10;
        
        if (tooltipX + tooltipWidth > w) tooltipX = mouseX - tooltipWidth - 10;
        if (tooltipY - tooltipHeight < 0) tooltipY = mouseY + tooltipHeight + 10;

        // Draw tooltip background
        ctx.fillStyle = "rgba(0, 0, 0, 0.8)";
        ctx.fillRect(tooltipX, tooltipY - tooltipHeight, tooltipWidth, tooltipHeight);

        // Draw tooltip text
        ctx.fillStyle = "#fff";
        ctx.textAlign = "left";
        ctx.fillText(text, tooltipX + 6, tooltipY - 8);

        // Highlight the nearest point
        const [px, py] = toPixel(x, y);
        const seriesIndex = Object.keys(data).indexOf(seriesName);
        const color = colors[seriesIndex % colors.length];
        
        ctx.strokeStyle = "#fff";
        ctx.fillStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(px, py, 6, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();
    };

    // Redraw function that includes hover effects
    const redrawWithHover = (mouseX, mouseY) => {
        // Redraw the base plot
        FUNC_NAME(canvas, data);
        
        // Add hover effects if mouse is over the plot area
        if (mouseX >= padding_left && mouseX <= w - padding_right && 
            mouseY >= padding_top && mouseY <= h - padding_bottom) {
            const nearestPoint = findNearestPoint(mouseX, mouseY);
            if (nearestPoint) {
                drawTooltip(mouseX, mouseY, nearestPoint);
            }
        }
    };

    // Mouse event handlers
    const handleMouseMove = (event) => {
        const rect = canvas.getBoundingClientRect();
        const mouseX = event.clientX - rect.left;
        const mouseY = event.clientY - rect.top;
        
        redrawWithHover(mouseX, mouseY);
    };

    const handleMouseLeave = () => {
        // Redraw without hover effects
        FUNC_NAME(canvas, data);
    };

    // Remove existing event listeners if any
    canvas.removeEventListener('mousemove', canvas._handleMouseMove);
    canvas.removeEventListener('mouseleave', canvas._handleMouseLeave);

    // Add new event listeners
    canvas._handleMouseMove = handleMouseMove;
    canvas._handleMouseLeave = handleMouseLeave;
    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);
}
window.FUNC_NAME = FUNC_NAME;
"""
