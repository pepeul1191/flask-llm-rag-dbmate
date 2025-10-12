<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { Modal } from 'bootstrap';
  import { fetchEngines } from '../services/engines_service.js';
  import { createProject, updateProject } from '../services/projects_service.js';

  export let project = null; // null para nuevo proyecto, objeto para editar

  let modalEl;
  let modalInstance;
  let engines = [];
  const dispatch = createEventDispatcher();

  // Campos del formulario, vinculados a project o vacíos para nuevo
  let id = '';
  let title = '';
  let description = '';
  let engineId = '';
  let connectionString = '';

  // Cuando cambia project, actualizar valores del formulario
  $: if (project) {
    id = project.id ?? '';
    title = project.title ?? '';
    description = project.description ?? '';
    engineId = project.engine?.id ?? '';
    connectionString = project.connection_string ?? '';
  } else {
    title = '';
    description = '';
    engineId = '';
    connectionString = '';
  }

  onMount(() => {
    modalInstance = new Modal(modalEl);
    
    fetchEngines().then((resp) => {
        engines = resp.data;
      }).catch((resp) =>  {
        console.log(resp);
      })
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
      title: title, 
      description: description, 
      connection_string: connectionString,
      engine_id: engineId
    };

    if(id == ''){
      createProject(savedProject).then((resp) => {
        console.log(resp.data);
      }).catch((resp) =>  {
        console.log(resp);
      })
    }else{
      updateProject(id, savedProject).then((resp) => {
        console.log(resp.data);
      }).catch((resp) =>  {
        console.log(resp);
      })
    }

    //dispatch('guardar', savedProject);
    //modalInstance.hide();
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

          <div class="row mb-3">
            <!-- Columna de 3 con el select -->
            <div class="col-md-3">
              <label for="projectEngine" class="form-label">Motor de Base de Datos</label>
              <select id="projectEngine" class="form-select" bind:value={engineId} required>
                <option value="">Seleccionar</option>
                {#each engines as engine (engine.id)}
                  <option value="{engine.id}">{engine.name}</option>
                {/each}
              </select>
            </div>

            <!-- Columna de 9 con el input -->
            <div class="col-md-9">
              <label for="connectionString" class="form-label">Cadena de Conexión (formato DBMate)</label>
              <input type="text" id="connectionString" class="form-control" bind:value={connectionString}>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button type="submit" class="btn btn-primary"><i class="fa fa-floppy-o" aria-hidden="true"></i> Guardar proyecto</button>
        </div>
      </form>
    </div>
  </div>
</div>
