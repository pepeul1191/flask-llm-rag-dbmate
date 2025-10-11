<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { Dropdown } from 'bootstrap';

  export let project;

  let dropdownInstance;
  let dropdownButtonEl;

  const dispatch = createEventDispatcher();

  function toggleDropdown() {
    dropdownInstance.toggle();
  }

  function handleEdit() {
    dispatch('edit', project);
  }

  function handleDelete() {
    dispatch('delete', project);
  }

  onMount(() => {
    dropdownInstance = new Dropdown(dropdownButtonEl);
  });
</script>

<div class="project-flex-card flex-fill" style="min-width: 300px; max-width: 400px;">
  <div class="card h-100 border-0 shadow-sm">
    <div class="card-body">
      <!-- Fila 1: Icono y menú de 3 puntos -->
      <div class="d-flex justify-content-between align-items-start mb-3">
        <!-- Icono del motor -->
        <div
          class="project-icon bg-opacity-10 rounded-3 d-flex align-items-center justify-content-center"
          style="width: 50px; height: 50px;"
        >
          <img src={project.engine.image_url} alt={project.engine.name} height="60" width="60" />
        </div>

        <!-- Dropdown menú -->
        <div class="dropdown">
          <button
            class="btn btn-link text-muted p-0 border-0"
            type="button"
            data-bs-toggle="dropdown"
            aria-expanded="false"
            on:click={toggleDropdown}
            bind:this={dropdownButtonEl}
          >
            <i class="fa fa-ellipsis-v fa-lg"></i>
          </button>
          <ul class="dropdown-menu dropdown-menu-end">
            <li>
              <a class="dropdown-item" href="#" on:click|preventDefault={handleEdit}>
                <i class="fa fa-pencil me-2"></i>Editar
              </a>
            </li>
            <li>
              <a class="dropdown-item" href="#" >
                <i class="fa fa-play me-2"></i>Continuar
              </a>
            </li>
            <li><hr class="dropdown-divider" /></li>
            <li>
              <a class="dropdown-item text-danger" href="#" on:click|preventDefault={handleDelete}>
                <i class="fa fa-trash me-2"></i>Eliminar
              </a>
            </li>
          </ul>
        </div>
      </div>

      <!-- Título -->
      <h5 class="card-title fw-bold text-dark mb-3" style="min-height: 3rem;">
        {project.title}
      </h5>

      <!-- Descripción -->
      <p>{project.description}</p>

      <!-- Fecha y versiones -->
      <div class="text-muted small d-flex justify-content-between align-items-center">
        <span>{project.date}</span>
        <span>{project.versions} versiones</span>
      </div>
    </div>
  </div>
</div>

<style>
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
    font-size: 1.4rem;
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
</style>
