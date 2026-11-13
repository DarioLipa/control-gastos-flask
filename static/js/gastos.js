// ==========================================================
// Dali_Gastos - Módulo de Gestión de Gastos
// ==========================================================

function openGastoModal(isEdit = false, data = null) {
  const modal = document.getElementById('modalGasto');
  const title = document.getElementById('modalGastoTitulo');
  const form = document.getElementById('formGasto');
  const catSelect = document.getElementById('gasto_categoria');
  const grupoOtro = document.getElementById('grupoDetalleOtro');
  const detalleOtroInput = document.getElementById('gasto_detalle_otro');

  if (!modal || !form) return;

  if (isEdit && data) {
    title.textContent = 'Editar Gasto';
    form.action = `/gastos/${data.id}/editar`;
    document.getElementById('gasto_fecha').value = data.fecha;
    document.getElementById('gasto_descripcion').value = data.descripcion;
    document.getElementById('gasto_monto').value = parseFloat(data.monto).toFixed(2);
    catSelect.value = data.categoria;

    if (data.categoria === 'Otros') {
      grupoOtro.style.display = 'flex';
      detalleOtroInput.value = data.detalle_otro || '';
    } else {
      grupoOtro.style.display = 'none';
      detalleOtroInput.value = '';
    }
  } else {
    title.textContent = 'Registrar Nuevo Gasto';
    form.action = '/gastos/crear';
    form.reset();
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('gasto_fecha').value = today;
    grupoOtro.style.display = 'none';
  }

  modal.classList.add('active');
}

function closeGastoModal() {
  const modal = document.getElementById('modalGasto');
  if (modal) modal.classList.remove('active');
}

// Mostrar u ocultar campo detalle de "Otros"
document.addEventListener('DOMContentLoaded', function() {
  const catSelect = document.getElementById('gasto_categoria');
  const grupoOtro = document.getElementById('grupoDetalleOtro');

  if (catSelect && grupoOtro) {
    catSelect.addEventListener('change', function() {
      if (this.value === 'Otros') {
        grupoOtro.style.display = 'flex';
      } else {
        grupoOtro.style.display = 'none';
      }
    });
  }

  // Filtrado instantáneo de la tabla de gastos
  const searchInput = document.getElementById('filtroBusqueda');
  if (searchInput) {
    searchInput.addEventListener('input', filtrarTablaGastos);
  }
});

function filtrarTablaGastos() {
  const filter = (document.getElementById('filtroBusqueda')?.value || '').toLowerCase();
  const table = document.getElementById('tablaGastos');
  if (!table) return;

  const rows = table.getElementsByTagName('tbody')[0]?.getElementsByTagName('tr') || [];
  for (let i = 0; i < rows.length; i++) {
    const textDesc = rows[i].querySelector('.col-desc')?.textContent || '';
    const textCat = rows[i].querySelector('.col-cat')?.textContent || '';
    if (textDesc.toLowerCase().includes(filter) || textCat.toLowerCase().includes(filter)) {
      rows[i].style.display = '';
    } else {
      rows[i].style.display = 'none';
    }
  }
}
