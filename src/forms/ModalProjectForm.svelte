<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { Modal } from 'bootstrap';
  import { fetchEngines } from '../services/engines_service.js';
  import { createProject, updateProject } from '../services/projects_service.js';
  import FlashAlert from '../components/FlashAlert.svelte';
  import { navigate } from 'svelte-routing';

  export let project = null;
  export let showContinue = true;

  let modalEl;
  let modalInstance;
  let engines = [];
  const dispatch = createEventDispatcher();
  const placeholders = [
    'sqlite3:db/database.db',
    'mysql://usuario:contraseña@localhost:3306/basedatos',
    'postgres://usuario:contraseña@localhost:5432/basedatos'
  ]

  // Campos del formulario
  let id = '';
  let title = '';
  let description = '';
  let engineId = '';
  let connectionString = '';

  // Bandera para controlar si estamos editando - ¡FALTABA ESTA DECLARACIÓN!
  let isEditing = false;

  // Estado para el flash alert
  let showAlert = false;
  let alertMessage = '';
  let alertType = 'success';

  // Solo actualizar valores iniciales cuando se abre el modal o project cambia
  $: if (project && !isEditing) {
    id = project.id ?? '';
    title = project.title ?? '';
    description = project.description ?? '';
    engineId = project.engine?.id ?? '';
    connectionString = project.connection_string ?? '';
  }

  onMount(() => {
    modalInstance = new Modal(modalEl);
    
    modalEl.addEventListener('show.bs.modal', () => {
      isEditing = false;
    });
    
    modalEl.addEventListener('hide.bs.modal', () => {
      isEditing = false;
    });

    fetchEngines().then((resp) => {
      engines = resp.data;
    }).catch((resp) => {
      console.log(resp);
    });
  });

  export function clear() {
    id = '';
    title = '';
    description = '';
    engineId = '';
    connectionString = '';
  }

  export function show() {
    modalInstance.show();
  }

  export function hide() {
    modalInstance.hide();
  }

  function startEditing() {
    isEditing = true;
  }

  function showFlashAlert(message, type = 'success') {
    alertMessage = message;
    alertType = type;
    showAlert = true;
  }

  function handleAlertClose() {
    showAlert = false;
    alertMessage = '';
  }

  async function onSubmit(event) {
    event.preventDefault();

    if (!title.trim() || !description.trim() || !engineId) {
      showFlashAlert('Por favor, completa todos los campos obligatorios.', 'danger');
      return;
    }

    const savedProject = {
      title: title, 
      description: description, 
      connection_string: connectionString,
      engine_id: engineId
    };

    try {
      if(id == ''){
        const resp = await createProject(savedProject);
        console.log(resp.data);
        id = resp.data.id;
        
        showFlashAlert(resp.message, 'success');
        
        dispatch('refreshList', resp.data);
      } else {
        const resp = await updateProject(id, savedProject);
        showFlashAlert(resp.message, 'success');
        
        dispatch('refreshList', resp.data);
      }
    } catch (resp) {
      console.log(resp);
      const errorMessage = resp?.error?.message || 'Ha ocurrido un error. Por favor, intenta nuevamente.';      
      showFlashAlert(errorMessage, 'danger');
    }
  }
</script>

<div class="modal fade" tabindex="-1" aria-labelledby="modalLabel" aria-hidden="true" bind:this={modalEl}>
  <div class="modal-dialog modal-lg modal-dialog-centered">
    <div class="modal-content">
    
      <form on:submit={onSubmit}>
        <div class="modal-header">
          <h5 class="modal-title" id="modalLabel">{id ? 'Editar proyecto' : 'Crear nuevo proyecto'}</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar" on:click={() => modalInstance.hide()}></button>
        </div>
        
        <div class="modal-body">
          {#if showAlert}
            <FlashAlert 
              message="{alertMessage}"
              type="{alertType}"
              duration={5000}
              position="absolute"
              on:close={handleAlertClose}
            />
          {/if}
          <div class="mb-3">
            <label for="projectTitle" class="form-label">Título</label>
            <input 
              id="projectTitle" 
              type="text" 
              class="form-control" 
              bind:value={title} 
              on:input={startEditing}
              placeholder="Ingresa el título del proyecto" 
              required 
            />
          </div>

          <div class="mb-3">
            <label for="projectDescription" class="form-label">Descripción</label>
            <textarea 
              id="projectDescription" 
              class="form-control" 
              rows="3" 
              bind:value={description} 
              on:input={startEditing}
              placeholder="Descripción del proyecto" 
              required
            ></textarea>
          </div>

          <div class="row mb-3">
            <div class="col-md-3">
              <label for="projectEngine" class="form-label">Motor de Base de Datos</label>
              <select 
                id="projectEngine" 
                class="form-select" 
                bind:value={engineId} 
                on:change={startEditing}
                required
              >
                <option value="">Seleccionar</option>
                {#each engines as engine (engine.id)}
                  <option value="{engine.id}">{engine.name}</option>
                {/each}
              </select>
            </div>

            <div class="col-md-9">
              <label for="connectionString" class="form-label">Cadena de Conexión (formato DBMate)</label>
              <input 
                type="text" 
                id="connectionString" 
                class="form-control" 
                bind:value={connectionString}
                on:input={startEditing}
                placeholder={placeholders[engineId-1]}
              />
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          {#if id && showContinue}
            <button 
              type="button" 
              class="btn btn-outline-primary"
              on:click={() => {
                modalInstance.hide();
                navigate(`/projects/${id}/edit`);
              }}>
              <i class="fa fa-search me-2" aria-hidden="true"></i> 
              Ver Proyecto
            </button>
          {/if}
          <button type="submit" class="btn btn-primary">
            <i class="fa fa-floppy-o me-2" aria-hidden="true"></i> 
            {id ? 'Actualizar proyecto' : 'Crear proyecto'}
          </button>
        </div>
      </form>
    </div>
  </div>
</div>