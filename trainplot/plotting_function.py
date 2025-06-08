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

    // Helper function to convert data coordinates to pixel coordinates
    const toPixel = (x, y) => [
        padding_left + (x - xmin) / (xmax - xmin) * plotWidth,
        padding_top + plotHeight - (y - ymin) / (ymax - ymin) * plotHeight
    ];

    // Color palette
    const colors = [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"
    ];

    // Draw grid
    ctx.strokeStyle = "#f0f0f0";
    ctx.lineWidth = 1;
    for (let i = 1; i < 5; i++) {
        const x = padding_left + (i / 5) * plotWidth;
        const y = padding_top + (i / 5) * plotHeight;
        ctx.beginPath();
        ctx.moveTo(x, padding_top);
        ctx.lineTo(x, padding_top + plotHeight);
        ctx.moveTo(padding_left, y);
        ctx.lineTo(padding_left + plotWidth, y);
        ctx.stroke();
    }

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
    ctx.textAlign = "center";
    for (let i = 0; i <= 5; i++) {
        const x = padding_left + (i / 5) * plotWidth;
        const value = xmin + (i / 5) * (xmax - xmin);
        ctx.fillText(value.toFixed(1), x, h - 10);
    }
    ctx.textAlign = "right";
    for (let i = 0; i <= 5; i++) {
        const y = padding_top + plotHeight - (i / 5) * plotHeight;
        const value = ymin + (i / 5) * (ymax - ymin);
        ctx.fillText(value.toFixed(2), padding_left - 10, y + 4);
    }

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
}
window.FUNC_NAME = FUNC_NAME;
"""
