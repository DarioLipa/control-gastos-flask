// ==========================================================
// Dali_Gastos - Visualización de Gráficos Financieros
// ==========================================================

document.addEventListener('DOMContentLoaded', function() {
  initDashboardCharts();
});

function initDashboardCharts() {
  if (typeof window.catLabels !== 'undefined' && typeof window.catValues !== 'undefined') {
    renderCategoryDonut('chartCategorias', window.catLabels, window.catValues);
  }

  if (typeof window.trendLabels !== 'undefined' && typeof window.trendValues !== 'undefined') {
    renderTrendChart('chartTendencia', window.trendLabels, window.trendValues);
  }
}

// 1. Gráfico de Dona para Categorías
function renderCategoryDonut(canvasId, labels, values) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = (rect.width || 420) * dpr;
  canvas.height = (rect.height || 260) * dpr;
  ctx.scale(dpr, dpr);

  const width = canvas.width / dpr;
  const height = canvas.height / dpr;

  ctx.clearRect(0, 0, width, height);

  const total = values.reduce((sum, v) => sum + v, 0);

  // Estado vacío
  if (total === 0 || values.length === 0) {
    ctx.fillStyle = '#94A3B8';
    ctx.font = '500 13px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('No hay gastos registrados en el período', width / 2, height / 2);
    return;
  }

  // Paleta de colores consistente para categorías
  const categoryColors = {
    'Alimentación': '#EA580C',
    'Transporte': '#2563EB',
    'Vivienda': '#4F46E5',
    'Servicios básicos': '#0891B2',
    'Salud': '#059669',
    'Educación': '#7C3AED',
    'Compras': '#DB2777',
    'Entretenimiento': '#9333EA',
    'Tecnología': '#0284C7',
    'Comunicación': '#0D9488',
    'Vestimenta': '#D97706',
    'Viajes': '#0E7490',
    'Deudas': '#DC2626',
    'Imprevistos': '#E11D48',
    'Otros': '#64748B'
  };

  const fallbackColors = ['#10B981', '#2563EB', '#8B5CF6', '#F59E0B', '#06B6D4', '#EC4899', '#64748B'];

  const centerX = width * 0.28;
  const centerY = height * 0.5;
  const outerRadius = Math.min(centerX, centerY) - 16;
  const innerRadius = outerRadius * 0.64;

  let startAngle = -Math.PI / 2;

  values.forEach((val, i) => {
    const label = labels[i];
    const sliceAngle = (val / total) * (Math.PI * 2);
    const endAngle = startAngle + sliceAngle;
    const color = categoryColors[label] || fallbackColors[i % fallbackColors.length];

    ctx.beginPath();
    ctx.arc(centerX, centerY, outerRadius, startAngle, endAngle);
    ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
    ctx.closePath();

    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 2;
    ctx.stroke();

    startAngle = endAngle;
  });

  // Centro de la dona (Suma en Soles)
  ctx.fillStyle = '#0F172A';
  ctx.font = '800 16px Inter, sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText('S/ ' + Math.round(total), centerX, centerY - 8);

  ctx.fillStyle = '#64748B';
  ctx.font = '600 10px Inter, sans-serif';
  ctx.fillText('TOTAL', centerX, centerY + 12);

  // Leyenda a la derecha
  const legendX = width * 0.56;
  const visibleItems = labels.slice(0, 6);
  const startY = Math.max(20, (height - (visibleItems.length * 26)) / 2 + 10);

  ctx.textAlign = 'left';
  ctx.textBaseline = 'middle';

  visibleItems.forEach((label, i) => {
    const y = startY + i * 26;
    const color = categoryColors[label] || fallbackColors[i % fallbackColors.length];
    const pct = Math.round((values[i] / total) * 100);

    // Cuadro de color
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(legendX + 6, y, 5, 0, Math.PI * 2);
    ctx.fill();

    // Texto de la categoría
    ctx.fillStyle = '#0F172A';
    ctx.font = '600 11.5px Inter, sans-serif';
    ctx.fillText(label, legendX + 16, y);

    // Porcentaje
    ctx.fillStyle = '#64748B';
    ctx.font = '500 11px Inter, sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText(`${pct}%`, width - 15, y);
    ctx.textAlign = 'left';
  });
}

// 2. Gráfico de Evolución Temporal
function renderTrendChart(canvasId, labels, values) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const dpr = window.devicePixelRatio || 1;
  const rect = canvas.getBoundingClientRect();

  canvas.width = (rect.width || 600) * dpr;
  canvas.height = (rect.height || 260) * dpr;
  ctx.scale(dpr, dpr);

  const width = canvas.width / dpr;
  const height = canvas.height / dpr;

  ctx.clearRect(0, 0, width, height);

  if (!values || values.length === 0) {
    ctx.fillStyle = '#94A3B8';
    ctx.font = '500 13px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Sin registros suficientes para graficar evolución', width / 2, height / 2);
    return;
  }

  const paddingLeft = 65;
  const paddingRight = 25;
  const paddingTop = 25;
  const paddingBottom = 40;

  const chartW = width - paddingLeft - paddingRight;
  const chartH = height - paddingTop - paddingBottom;

  const maxVal = Math.max(...values, 50) * 1.15;
  const minVal = 0;

  // Líneas de cuadrícula
  const gridSteps = 4;
  ctx.strokeStyle = '#F1F5F9';
  ctx.lineWidth = 1;
  ctx.fillStyle = '#94A3B8';
  ctx.font = '500 11px Inter, sans-serif';
  ctx.textAlign = 'right';

  for (let i = 0; i <= gridSteps; i++) {
    const y = paddingTop + (chartH / gridSteps) * i;
    const val = maxVal - (maxVal / gridSteps) * i;

    ctx.beginPath();
    ctx.moveTo(paddingLeft, y);
    ctx.lineTo(width - paddingRight, y);
    ctx.stroke();

    ctx.fillText('S/ ' + Math.round(val), paddingLeft - 10, y + 4);
  }

  // Puntos
  const points = values.map((val, idx) => {
    const x = paddingLeft + (chartW / (values.length - 1 || 1)) * idx;
    const y = paddingTop + chartH - ((val - minVal) / (maxVal - minVal)) * chartH;
    return { x, y, val, label: labels[idx] };
  });

  // Área sombreada con degradado esmeralda / azul
  const grad = ctx.createLinearGradient(0, paddingTop, 0, paddingTop + chartH);
  grad.addColorStop(0, 'rgba(16, 185, 129, 0.22)');
  grad.addColorStop(1, 'rgba(16, 185, 129, 0.01)');

  ctx.beginPath();
  ctx.moveTo(points[0].x, paddingTop + chartH);
  points.forEach(p => ctx.lineTo(p.x, p.y));
  ctx.lineTo(points[points.length - 1].x, paddingTop + chartH);
  ctx.closePath();
  ctx.fillStyle = grad;
  ctx.fill();

  // Línea principal
  ctx.beginPath();
  ctx.moveTo(points[0].x, points[0].y);
  for (let i = 1; i < points.length; i++) {
    ctx.lineTo(points[i].x, points[i].y);
  }
  ctx.strokeStyle = '#10B981';
  ctx.lineWidth = 3;
  ctx.stroke();

  // Puntos en la línea
  ctx.textAlign = 'center';
  points.forEach((p, idx) => {
    ctx.beginPath();
    ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = '#FFFFFF';
    ctx.fill();
    ctx.strokeStyle = '#1E3A8A';
    ctx.lineWidth = 2.5;
    ctx.stroke();

    // Etiqueta del eje X
    if (points.length <= 10 || idx % 2 === 0 || idx === points.length - 1) {
      ctx.fillStyle = '#64748B';
      ctx.font = '500 10.5px Inter, sans-serif';
      const labelShort = p.label.length > 5 ? p.label.substring(5) : p.label;
      ctx.fillText(labelShort, p.x, height - 12);
    }
  });
}
