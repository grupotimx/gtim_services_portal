<script lang="ts">
  import { onMount, tick } from 'svelte';
  import Chart from 'chart.js/auto';
  import type { ChartType } from 'chart.js';
  import ChartDataLabels from 'chartjs-plugin-datalabels';

  let chart: Chart;
  let canvas: HTMLCanvasElement;

  let chartType: ChartType = 'bar';
  let tipoGrafica = 'diaria';
  let fechaInicio = '';
  let fechaFin = '';
  let grupoTimbrado = '';
  let chartData = { labels: [], datasets: [] };
  let loading = false;

  // Login
  let usuario = '';
  let contrasena = '';
  let logueado = false;
  let errorLogin = false;

  function login() {
    if (usuario === 'admin' && contrasena === 'admin') {
      logueado = true;
      errorLogin = false;
      cargarDatos();
    } else {
      errorLogin = true;
    }
  }

  Chart.register(ChartDataLabels);

  async function cargarDatos() {
    loading = true;
    let url = '';
    const params = new URLSearchParams();

    if (fechaInicio) params.append('fecha_inicio', fechaInicio);
    if (fechaFin) params.append('fecha_fin', fechaFin);
    if (grupoTimbrado) params.append('grupo', grupoTimbrado);

    switch (tipoGrafica) {
      case 'mensual':
        url = 'http://localhost:8000/llamadas/resumen-mensual';
        break;
      case 'por_agente':
        url = 'http://localhost:8000/llamadas/por-agente?estado=contestada';
        break;
      case 'por_agente_no':
        url = 'http://localhost:8000/llamadas/por-agente?estado=no_contestada';
        break;
      case 'duracion':
        url = 'http://localhost:8000/llamadas/duracion-por-agente';
        break;
      case 'diaria':
      default:
        url = `http://localhost:8000/llamadas/stacked-por-turno?${params.toString()}`;
        break;
    }

    try {
      const res = await fetch(url);
      const result = await res.json();

      if (tipoGrafica === 'mensual') {
        chartData = {
          labels: result.map(r => r.mes),
          datasets: [{ label: 'Llamadas por mes', data: result.map(r => r.total), backgroundColor: '#007bff' }]
        };
      } else if (tipoGrafica.includes('agente')) {
        chartData = {
          labels: result.map(r => r.extension),
          datasets: [{ label: 'Llamadas por agente', data: result.map(r => r.total), backgroundColor: '#28a745' }]
        };
      } else if (tipoGrafica === 'duracion') {
        chartData = {
          labels: result.map(r => r.extension),
          datasets: [{ label: 'Duración promedio', data: result.map(r => Math.round(r.promedio)), backgroundColor: '#ffc107' }]
        };
      } else {
        chartData = {
          labels: [...result.labels].reverse(),
          datasets: result.datasets.map(ds => ({
            ...ds,
            data: [...ds.data].reverse(),
            categoryPercentage: 0.7,
            barPercentage: 1
          }))
        };
      }
    } catch (error) {
      console.error('Error al cargar los datos:', error);
    } finally {
      loading = false;
      await tick();
      if (canvas) renderChart();
    }
  }

  function renderChart() {
    if (chart) chart.destroy();

    chart = new Chart(canvas, {
      type: chartType,
      data: chartData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: true },
          datalabels: {
            display: context => context.datasetIndex === chartData.datasets.length - 1,
            formatter: (value, context) => {
              if (tipoGrafica === 'duracion') {
                return value >= 60 ? `${Math.round(value / 60)} min` : `${Math.round(value)} segs`;
              } else {
                const index = context.dataIndex;
                const datasets = context.chart.data.datasets;
                let total = 0;
                for (let i = 0; i < datasets.length; i++) {
                  total += +datasets[i].data[index];
                }
                return total;
              }
            },
            color: 'black',
            anchor: 'end',
            align: 'end',
            font: { weight: 'bold', size: 11 }
          }
        },
        scales: {
          x: {
            stacked: true,
            ticks: {
              maxRotation: 45,
              minRotation: 45,
              autoSkip: false,
              font: { size: 10 }
            }
          },
          y: { stacked: true }
        }
      },
      plugins: [ChartDataLabels]
    });
  }

  function actualizarGrafica() {
    cargarDatos();
  }

  onMount(() => {
    if (logueado) cargarDatos();
  });
</script>

{#if !logueado}
  <div class="min-vh-100 d-flex justify-content-center align-items-center bg-light">
    <div class="card p-4 shadow" style="width: 300px;">
      <h5 class="mb-3 text-center">Iniciar sesión</h5>
      <input class="form-control mb-2" placeholder="Usuario" bind:value={usuario} />
      <input class="form-control mb-3" placeholder="Contraseña" type="password" bind:value={contrasena} />
      {#if errorLogin}
        <div class="text-danger text-center mb-2">Credenciales incorrectas</div>
      {/if}
      <button class="btn btn-primary w-100" on:click={login}>Entrar</button>
    </div>
  </div>
{:else}
<div class="container-fluid min-vh-100 bg-light p-0">
  <header class="d-flex justify-content-between align-items-center px-4 py-2 bg-light border-bottom">
    <h2 class="fw-bold mb-0" style="font-size: 1.5rem; color: #1a237e;">Portal de Servicios Administrados</h2>
    <img src="/logo.png" alt="Logo GTIM" class="img-fluid" style="height: 50px;" />
  </header>

  <div class="row g-0">
    <aside class="col-md-2 bg-white border-end p-3">
      <h4 class="mb-4">Menú</h4>
      <ul class="nav flex-column">
        <li class="nav-item">
          <a class="nav-link active" href="#">Inicio</a>
        </li>
      </ul>
    </aside>

    <main class="col-md-10 p-4 bg-white">
      <section>
        <h4 class="mb-3">PBX</h4>

        <div class="row g-2 align-items-end mb-4">
          <div class="col-md-2">
            <label class="form-label">Fecha Inicio</label>
            <input type="date" bind:value={fechaInicio} class="form-control" />
          </div>
          <div class="col-md-2">
            <label class="form-label">Fecha Fin</label>
            <input type="date" bind:value={fechaFin} class="form-control" />
          </div>
          <div class="col-md-3">
            <label class="form-label">Grupo Timbrado</label>
            <input type="text" bind:value={grupoTimbrado} class="form-control" />
          </div>
          <div class="col-md-3">
            <label class="form-label">Tipo de Gráfica</label>
            <select bind:value={tipoGrafica} class="form-select">
              <option value="diaria">Gráfica diaria</option>
              <option value="mensual">Gráfica mensual</option>
              <option value="por_agente">Por agente (contestadas)</option>
              <option value="por_agente_no">Por agente (no contestadas)</option>
              <option value="duracion">Duración por agente</option>
            </select>
          </div>
          <div class="col-md-1">
            <label class="form-label">Tipo</label>
            <select bind:value={chartType} class="form-select">
              <option value="bar">Barras</option>
              <option value="line">Línea</option>
              <option value="pie">Pastel</option>
              <option value="doughnut">Dona</option>
              <option value="radar">Radar</option>
            </select>
          </div>
          <div class="col-md-1 d-grid">
            <button class="btn btn-outline-primary" on:click={actualizarGrafica}>Filtrar</button>
          </div>
        </div>

        <div class="overflow-auto">
          {#if loading}
            <div class="text-center my-4">
              <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Cargando...</span>
              </div>
            </div>
          {:else}
            {#if tipoGrafica === 'diaria' && (chartType === 'bar' || chartType === 'line')}
              <div style="overflow-x: auto;">
                <div style="min-width: 1000px; width: 3200px;">
                  <canvas bind:this={canvas} style="width: 100%; height: 450px;"></canvas>
                </div>
              </div>
            {:else}
              <canvas bind:this={canvas} style="width: 100%; height: 450px;"></canvas>
            {/if}
          {/if}
        </div>
      </section>

      <footer class="text-end mt-4 text-muted">
        www.grupotimexico.com
      </footer>
    </main>
  </div>
</div>
{/if}

<style>
  :global(body) {
    margin: 0;
    background-color: #f8f9fa;
  }
</style> 