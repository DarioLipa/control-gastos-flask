// ==========================================================
// GestorGastos - Script de Gráficos e Interactividad
// ==========================================================

document.addEventListener('DOMContentLoaded', function() {
  initCharts();
});

function initCharts() {
  if (typeof chartLabels === 'undefined' || typeof chartValues === 'undefined') return;

  renderTrendChart('chartTendencia', chartLabels, chartValues);
  renderDonutChart('chartCategorias', catLabels, catValues);
}

// 1. Gráfico de Tendencia Lineal (Canvas Puro de Alta Fidelidad)
function renderTrendChart(canvasId, labels, values) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  
  canvas.width = (rect.width || 680) * dpr;
  canvas.height = (rect.height || 260) * dpr;
  ctx.scale(dpr, dpr);

  const width = canvas.width / dpr;
  const height = canvas.height / dpr;

  const paddingLeft = 60;
  const paddingRight = 30;
  const paddingTop = 25;
  const paddingBottom = 40;

  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;

  const maxVal = Math.max(...values, 100) * 1.15;
  const minVal = 0;

  // Fondo y líneas de cuadrícula horizontales
  ctx.clearRect(0, 0, width, height);
  const gridSteps = 4;
  ctx.strokeStyle = 'rgba(14, 116, 144, 0.08)';
  ctx.lineWidth = 1;
  ctx.fillStyle = '#64748B';
  ctx.font = '11px Inter, sans-serif';
  ctx.textAlign = 'right';

  for (let i = 0; i <= gridSteps; i++) {
    const y = paddingTop + (chartH / gridSteps) * i;
    const val = maxVal - (maxVal / gridSteps) * i;

    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(width - paddingRight, y);
    ctx.stroke();

    ctx.fillText('$' + Math.round(val), paddingLeft - 10, y + 4);
  }

  if (values.length === 0) return;

  // Coordenadas de los puntos
  const points = values.map((val, idx) => {
    const x = paddingLeft + (chartW / (values.length - 1 || 1)) * idx;
    const y = paddingTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    return { x, y, val, label: labels[idx] };
  });

  // Área con gradiente
  const gradient = ctx.createLinearGradient(0, paddingTop, 0, paddingTop + chartH);
  gradient.addColorStop(0, 'rgba(14, 116, 144, 0.28)');
  gradient.addColorStop(1, 'rgba(240, 253, 255, 0.02)');

  ctx.beginPath();
  ctx.moveTo(points[0].x, paddingTop + chartH);
  points.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.lineTo(points[points.length - 1].x, paddingTop + chartH);
  ctx.closePath();
  ctx.fillStyle = gradient;
  ctx.fill();

  // Línea principal
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.strokeStyle = '#0E7490';
  ctx.lineWidth = 3;
  ctx.lineCap = 'round';
  ctx.lineJoin = 'round';
  ctx.stroke();

  // Puntos y etiquetas en el eje X
  ctx.textAlign = 'center';
  points.forEach((p, idx) => {
    // Círculo exterior (halo)
    ctx.beginPath();
    ctx.arc(p.x, p.y, 6, 0, Math.PI * 2);
    ctx.fillStyle = '#BAE6FD';
    ctx.fill();

    // Círculo interior
    ctx.beginPath();
    ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
    ctx.fillStyle = '#082F49';
    ctx.fill();

    // Etiqueta X (mostrar cada 1 o 2 puntos para que no se superpongan)
    if (points.length <= 8 || idx % 2 === 0 || idx === points.length - 1) {
      ctx.fillStyle = '#475569';
      ctx.font = '500 10.5px Inter, sans-serif';
      ctx.fillText(p.label.substring(5), p.x, height - 12);
    }
  });
}

// 2. Gráfico de Dona para Categorías (Canvas Puro con Leyenda)
function renderDonutChart(canvasId, labels, values) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();
  
  canvas.width = (rect.width || 380) * dpr;
  canvas.height = (rect.height || 260) * dpr;
  ctx.scale(dpr, dpr);

  const width = canvas.width / dpr;
  const height = canvas.height / dpr;

  ctx.clearRect(0, 0, width, height);

  const total = values.reduce((a, b) => a + b, 0);
  if (total === 0) return;

  const colors = [
    '#082F49', '#0E7490', '#22C55E', '#38BDF8', '#F59E0B', '#8B5CF6', '#EC4899', '#64748B'
  ];

  const centerX = width * 0.35;
  const centerY = height * 0.5;
  const outerRadius = Math.min(centerX, centerY) - 15;
  const innerRadius = outerRadius * 0.62;

  let startAngle = -Math.PI / 2;

  values.forEach((val, i) => {
    const sliceAngle = (val / total) * (Math.PI * 2);
    const endAngle = startAngle + sliceAngle;

    ctx.beginPath();
    ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
    ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
    ctx.closePath();

    ctx.fillStyle = colors[i % colors.length];
    ctx.fill();
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    startAngle = endAngle;
  });

  // Centro de la dona (Métrica resumida)
  ctx.fillStyle = '#082F49';
  ctx.font = '700 15px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('$' + Math.round(total), centerX, centerY - 8);

  ctx.fillStyle = '#64748B';
  ctx.font = '500 10px Inter, sans-serif';
  ctx.fillText('TOTAL', centerX, centerY + 10);

  // Leyenda a la derecha
  const legendX = width * 0.62;
  const startY = Math.max(20, (height - (labels.length * 24)) / 2 + 10);
  
  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';

  labels.slice(0, 7).forEach((label, i) => {
    const y = startY + i * 24;
    const color = colors[i % colors.length];
    const pct = Math.round((values[i] / total) * 100);

    // Cuadrito de color redondeado
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(legendX, y - 5, 10, 10, 3) : ctx.rect(legendX, y - 5, 10, 10);
    ctx.fill();

    // Texto de categoría
    ctx.fillStyle = '#082F49';
    ctx.font = '600 11px Inter, sans-serif';
    ctx.fillText(label, legendX + 16, y);

    // Porcentaje
    ctx.fillStyle = '#64748B';
    ctx.font = '500 10.5px Inter, sans-serif';
    ctx.fillText(`${pct}%`, width - 25, y);
  });
}
