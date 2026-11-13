// ==========================================================
// Dali_Gastos - Motor de Gráficos Financieros
// Reproducción Fiel del Gráfico de Área con Curva y Degradado
// ==========================================================

document.addEventListener('DOMContentLoaded', function() {
  initMainAreaChart();
});

function initMainAreaChart() {
  const canvas = document.getElementById('chartEvolucionPrincipal');
  if (!canvas) return;

  const rawLabels = window.trendLabels || [];
  const rawValues = window.trendValues || [];

  if (rawValues.length === 0) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;

  function resizeAndDraw() {
    const rect = canvas.parentElement.getBoundingClientRect();
    const width = rect.width;
    const height = Math.max(rect.height, 320);

    canvas.width = width * dpr;
    canvas.height = height * dpr;
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';

    ctx.resetTransform ? ctx.resetTransform() : ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);

    drawChart(ctx, width, height, rawLabels, rawValues);
  }

  window.addEventListener('resize', resizeAndDraw);
  resizeAndDraw();

  // Interactividad y Tooltips
  let activeTooltip = null;

  canvas.addEventListener('mousemove', function(e) {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const points = canvas._chartPoints || [];
    let closest = null;
    let minDistance = 25;

    points.forEach(p => {
      const dist = Math.hypot(p.x - mouseX, p.y - mouseY);
      if (dist < minDistance) {
        minDistance = dist;
        closest = p;
      }
    });

    if (closest !== activeTooltip) {
      activeTooltip = closest;
      resizeAndDraw();
      if (closest) {
        drawTooltip(ctx, closest);
      }
    }
  });

  canvas.addEventListener('mouseleave', function() {
    if (activeTooltip) {
      activeTooltip = null;
      resizeAndDraw();
    }
  });
}

function drawChart(ctx, width, height, labels, values) {
  ctx.clearRect(0, 0, width, height);

  const padLeft = 65;
  const padRight = 30;
  const padTop = 30;
  const padBottom = 45;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const maxVal = Math.max(...values, 100) * 1.15;
  const minVal = 0;

  // 1. Líneas de Cuadrícula Horizontales y Eje Y
  const gridSteps = 4;
  ctx.strokeStyle = '#F1F5F9';
  ctx.lineWidth = 1;
  ctx.fillStyle = '#94A3B8';
  ctx.font = '500 11px Inter, sans-serif';
  ctx.textAlign = 'right';

  for (let i = 0; i <= gridSteps; i++) {
    const y = padTop + (chartH / gridSteps) * i;
    const val = maxVal - (maxVal / gridSteps) * i;

    ctx.beginPath();
    ctx.moveTo(padLeft, y);
    ctx.lineTo(width - padRight, y);
    ctx.stroke();

    ctx.fillText('S/ ' + Math.round(val), padLeft - 12, y + 4);
  }

  if (values.length === 0) return;

  // 2. Coordenadas de los Puntos
  const points = values.map((val, idx) => {
    const x = padLeft + (chartW / (values.length - 1 || 1)) * idx;
    const y = padTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    return { x, y, val, label: labels[idx] };
  });

  // Guardar puntos para interacción con cursor
  ctx.canvas._chartPoints = points;

  // 3. Trazado del Área con Curva Suavizada (Catmull-Rom / Spline Cúbico)
  const spline = getSplinePath(points);

  // Área con Degradado Fucsia -> Morado -> Azul Profundo (Exacto a la Imagen 1)
  const areaGrad = ctx.createLinearGradient(0, padTop, 0, padTop + chartH);
  areaGrad.addColorStop(0, '#F326A5');
  areaGrad.addColorStop(0.45, '#A500D6');
  areaGrad.addColorStop(1, '#3021C5');

  ctx.save();
  ctx.beginPath();
  ctx.moveTo(points[0].x, padTop + chartH);
  ctx.lineTo(points[0].x, points[0].y);
  spline(ctx);
  ctx.lineTo(points[points.length - 1].x, padTop + chartH);
  ctx.closePath();
  ctx.fillStyle = areaGrad;
  ctx.fill();
  ctx.restore();

  // 4. Línea de Contorno Superior Suavizada
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  spline(ctx);
  ctx.strokeStyle = '#FFFFFF';
  ctx.lineWidth = 3.5;
  ctx.stroke();
  ctx.restore();

  // 5. Puntos de Datos y Eje X
  ctx.textAlign = 'center';
  points.forEach((p, idx) => {
    // Halo blanco
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
    ctx.fillStyle = '#FFFFFF';
    ctx.fill();

    // Centro fucsia/morado
    ctx.beginPath();
    ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = '#A500D6';
    ctx.fill();

    // Etiqueta de fecha (Formato: DD/MM o DD Mes)
    ctx.fillStyle = '#64748B';
    ctx.font = '600 11px Inter, sans-serif';
    let dateStr = p.label;
    if (dateStr.includes('-')) {
      const parts = dateStr.split('-');
      const meses = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Set', 'Oct', 'Nov', 'Dic'];
      const mIdx = parseInt(parts[1], 10) - 1;
      dateStr = `${parts[2]} ${meses[mIdx] || parts[1]}`;
    }
    ctx.fillText(dateStr, p.x, height - 14);
  });
}

// Función para generar curvas cúbicas suaves (Spline)
function getSplinePath(points) {
  return function(ctx) {
    if (points.length < 2) return;
    for (let i = 0; i < points.length - 1; i++) {
      const p0 = points[i === 0 ? i : i - 1];
      const p1 = points[i];
      const p2 = points[i + 1];
      const p3 = points[i + 2 < points.length ? i + 2 : i + 1];

      const cp1x = p1.x + (p2.x - p0.x) / 6;
      const cp1y = p1.y + (p2.y - p0.y) / 6;
      const cp2x = p2.x - (p3.x - p1.x) / 6;
      const cp2y = p2.y - (p3.y - p1.y) / 6;

      ctx.bezierCurveTo(cp1x, cp1y, cp2x, cp2y, p2.x, p2.y);
    }
  };
}

// Tooltip flotante con información del gasto
function drawTooltip(ctx, point) {
  ctx.save();
  const text = `S/ ${point.val.toFixed(2)}`;
  ctx.font = '700 12px Inter, sans-serif';
  const width = ctx.measureText(text).width + 24;
  const height = 28;

  let x = point.x - width / 2;
  let y = point.y - height - 12;

  // Marco oscuro redondeado
  ctx.fillStyle = '#0F172A';
  ctx.beginPath();
  ctx.roundRect ? ctx.roundRect(x, y, width, height, 6) : ctx.rect(x, y, width, height);
  ctx.fill();

  // Flecha indicadora
  ctx.beginPath();
  ctx.moveTo(point.x - 5, y + height);
  ctx.lineTo(point.x + 5, y + height);
  ctx.lineTo(point.x, y + height + 5);
  ctx.closePath();
  ctx.fill();

  // Texto
  ctx.fillStyle = '#FFFFFF';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(text, point.x, y + height / 2);
  ctx.restore();
}
