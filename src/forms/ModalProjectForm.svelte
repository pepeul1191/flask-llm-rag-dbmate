<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { Modal } from 'bootstrap';

  export let project = null; // null para nuevo proyecto, objeto para editar

  let modalEl;
  let modalInstance;
  const dispatch = createEventDispatcher();

  // Campos del formulario, vinculados a project o vacíos para nuevo
  let title = '';
  let description = '';
  let engineId = '';

  // Cuando cambia project, actualizar valores del formulario
  $: if (project) {
    title = project.title ?? '';
    description = project.description ?? '';
    engineId = project.engine?.id ?? '';
  } else {
    title = '';
    description = '';
    engineId = '';
  }

  onMount(() => {
    modalInstance = new Modal(modalEl);
  });

  export function show() {
    modalInstance.show();
  }

  export function hide() {
    modalInstance.hide();
  }

  function onSubmit(event) {
    event.preventDefault();

    if (!title.trim() || !description.trim() || !engineId) {
      alert('Por favor, completa todos los campos.');
      return;
    }

    // Crear objeto proyecto guardado
    const savedProject = {
      ...project,
      title,
      description,
      engine: {
        id: +engineId,
        name: engineId == 1 ? 'SQLite3' : engineId == 2 ? 'MySQL' : 'Postgres',
        image_url: engineId == 1 ? '/img/sqlite.png' : engineId == 2 ? '/img/mysql.png' : '/img/postgres.png'
      }
    };

    dispatch('guardar', savedProject);
    modalInstance.hide();
  }
</script>

<div class="modal fade" tabindex="-1" aria-labelledby="modalLabel" aria-hidden="true" bind:this={modalEl}>
  <div class="modal-dialog modal-lg modal-dialog-centered">
    <div class="modal-content">
      <form on:submit={onSubmit}>
        <div class="modal-header">
          <h5 class="modal-title" id="modalLabel">{project ? 'Editar proyecto' : 'Crear nuevo proyecto'}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar" on:click={() => modalInstance.hide()}></button>
        </div>
        <div class="modal-body">
          <div class="mb-3">
            <label for="projectTitle" class="form-label">Título</label>
            <input id="projectTitle" type="text" class="form-control" bind:value={title} placeholder="Ingresa el título del proyecto" required />
          </div>

          <div class="mb-3">
            <label for="projectDescription" class="form-label">Descripción</label>
            <textarea id="projectDescription" class="form-control" rows="3" bind:value={description} placeholder="Descripción del proyecto" required></textarea>
          </div>

          <div class="mb-3">
            <label for="projectEngine" class="form-label">Motor de Base de Datos</label>
            <select id="projectEngine" class="form-select" bind:value={engineId} required>
              <option value="">Seleccionar motor</option>
              <option value="1">SQLite3</option>
              <option value="2">MySQL</option>
              <option value="3">Postgres</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button type="submit" class="btn btn-primary"><i class="fa fa-floppy-o" aria-hidden="true"></i> Guardar proyecto</button>
        </div>
      </form>
    </div>
  </div>
</div>
