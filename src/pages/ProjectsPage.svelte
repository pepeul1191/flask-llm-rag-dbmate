<script>
  import { onMount } from 'svelte';
  import { Modal } from 'bootstrap';

  let createModal;

  // Inicializar el modal cuando el componente esté montado
  onMount(() => {
    const modalEl = document.getElementById('createProjectModal');
    createModal = new Modal(modalEl);
  });

  function createProject() {
    if (createModal) {
      createModal.show();
    } else {
      console.warn("Modal no inicializado.");
    }
  }

  let projects = [
    {
      id: 1,
      title: "COA Concurso de Fotografía",
      description: "El sistema RAG en nuestra aplicación funciona como el motor inteligente que asiste al LLM a convertir diagramas PlantUML en código SQL mediante un proceso contextualizado.",
      date: "20 jun 2025",
      versions: 44,
      engine: {
        id: 1,
        name: 'SQLite3', 
        image_url: '/img/sqlite.png'
      }
    },
    {
      id: 2,
      title: "Innnova Rails", 
      description: "La Aplicación Web recibe el diagrama PlantUML y parámetros del usuario, enviándolos al Operador de Embedding que genera representaciones vectoriales del modelo. ",
      date: "15 jun 2025",
      versions: 32,
      engine: {
        id: 2,
        name: 'MySQL', 
        image_url: '/img/mysql.png'
      }
    },
    {
      id: 3,
      title: "Quinua Smart",
      description: "El Constructor de Prompt integra entonces el PlantUML original con el contexto enriquecido obtenido, creando un prompt ampliado que se envía al LLM.",
      date: "10 jun 2025",
      versions: 28,
      engine: {
        id: 3,
        name: 'Postgres', 
        image_url: '/img/postgres.png'
      }

    }
  ];
</script>

<svelte:head>
  <title>Crear Proyecto</title>
</svelte:head>

<div class="projects-simple w-100">
  <!-- Header -->
  <div class="d-flex justify-content-between align-items-center mb-4 px-3">
    <h2 class="h4 fw-bold text-dark mb-0">Proyectos recientes</h2>
    <button class="btn btn-primary d-flex align-items-center" on:click={createProject}>
      <i class="fa fa-plus"></i>
      Crear proyecto
    </button>
  </div>

  <!-- Separador -->
  <hr class="my-4 mx-3" />

  <!-- Tarjetas en flexbox -->
  <div class="projects-flex-container w-100 d-flex flex-wrap gap-3 px-3">
    <!-- Tarjeta para crear nuevo -->
    <div class="project-flex-card flex-fill" style="min-width: 300px; max-width: 400px;"  on:click={createProject}>
      <div class="card h-100 border-2 border-dashed bg-light">
        <div class="card-body d-flex flex-column align-items-center justify-content-center text-center text-muted">
          <i class="fa fa-plus fa-2x mb-2"></i>
          <span class="fw-bold">Crear proyecto</span>
        </div>
      </div>
    </div>
    {#each projects as project}
      <div class="project-flex-card flex-fill" style="min-width: 300px; max-width: 400px;">
        <div class="card h-100 border-0 shadow-sm">
          <div class="card-body">
            <!-- Fila 1: Icono y menú de 3 puntos -->
            <div class="d-flex justify-content-between align-items-start mb-3">
              <!-- Icono a la izquierda -->
              <div class="project-icon bg-opacity-10 rounded-3 d-flex align-items-center justify-content-center" 
                  style="width: 50px; height: 50px;">
                <img src="{project.engine.image_url}" alt="{project.engine.name}" height="60" width="60">
              </div>
              
              <!-- Menú de 3 puntos a la derecha -->
              <div class="dropdown">
                <button class="btn btn-link text-muted p-0 border-0" type="button" 
                        data-bs-toggle="dropdown" aria-expanded="false">
                  <i class="fa fa-ellipsis-v fa-lg"></i>
                </button>
                <ul class="dropdown-menu dropdown-menu-end">
                  <li><a class="dropdown-item" href="#"><i class="fa fa-pencil me-2"></i>Editar</a></li>
                  <li><a class="dropdown-item" href="#"><i class="fa fa-play me-2"></i>Continuar</a></li>
                  <li><hr class="dropdown-divider"></li>
                  <li><a class="dropdown-item text-danger" href="#"><i class="fa fa-trash me-2"></i>Eliminar</a></li>
                </ul>
              </div>
            </div>

            <!-- Fila 2: Título del proyecto -->
            <h5 class="card-title fw-bold text-dark mb-3" style="min-height: 3rem;">
              {project.title}
            </h5>
            <p>{project.description}</p>
            <!-- Fila 3: Fecha y versiones -->
            <div class="text-muted small d-flex justify-content-between align-items-center">
              <span>{project.date}</span>
              <span>{project.versions} versiones</span>
            </div>
          </div>
        </div>
      </div>
    {/each}
  </div>
</div>

<!-- Modal: Crear Proyecto -->
<div class="modal fade" id="createProjectModal" tabindex="-1" aria-labelledby="createProjectModalLabel" aria-hidden="true">
  <div class="modal-dialog modal-lg modal-dialog-centered">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="createProjectModalLabel">Crear nuevo proyecto</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar"></button>
      </div>
      <div class="modal-body">
        <form id="projectForm">
          <div class="mb-3">
            <label for="projectTitle" class="form-label">Título</label>
            <input type="text" class="form-control" id="projectTitle" placeholder="Ingresa el título del proyecto" required>
          </div>

          <div class="mb-3">
            <label for="projectDescription" class="form-label">Descripción</label>
            <textarea class="form-control" id="projectDescription" rows="3" placeholder="Descripción del proyecto" required></textarea>
          </div>

          <div class="mb-3">
            <label for="projectEngine" class="form-label">Motor de Base de Datos</label>
            <select class="form-select" id="projectEngine" required>
              <option value="">Seleccionar motor</option>
              <option value="1">SQLite3</option>
              <option value="2">MySQL</option>
              <option value="3">Postgres</option>
            </select>
          </div>

          <div class="text-end">
            <button type="submit" class="btn btn-primary"> <i class="fa fa-floppy-o" aria-hidden="true"></i> Guardar proyecto</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</div>

<style>
  .projects-simple {
    width: 100%;
    margin-bottom: 50px;
    padding-top: 10px;
  }

  .projects-flex-container {
    gap: 1.5rem;
  }

  .project-flex-card .card {
    transition: all 0.3s ease;
    border-radius: 8px;
    min-height: 150px;
  }

  .project-flex-card .card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.1) !important;
  }

  .border-dashed {
    border-style: dashed !important;
    border-color: #adb5bd !important;
    cursor: pointer;
  }

  .border-dashed:hover {
    border-color: #0d6efd !important;
    background: #f8f9fa !important;
  }

  .card-title {
    font-size: 1rem;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  @media (max-width: 768px) {
    .projects-flex-container {
      gap: 1rem;
    }
    
    .project-flex-card {
      min-width: 100% !important;
      max-width: 100% !important;
    }
  }

   .project-flex-card .card {
    transition: all 0.3s ease;
    border-radius: 12px;
  }

  .project-flex-card .card:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.12) !important;
  }

  .project-icon {
    transition: all 0.3s ease;
  }

  .project-flex-card .card:hover .project-icon {
    transform: scale(1.1);
    background-color: rgba(13, 110, 253, 0.15) !important;
  }

  .card-title {
    font-size: 1rem;
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .dropdown-menu {
    border: none;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border-radius: 8px;
  }

  .dropdown-item {
    padding: 0.5rem 1rem;
    font-size: 0.875rem;
  }

  .dropdown-item:hover {
    
  }
</style>