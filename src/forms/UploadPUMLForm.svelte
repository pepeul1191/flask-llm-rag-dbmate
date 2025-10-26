<script>
  import { onMount, createEventDispatcher } from 'svelte';
  import { Modal } from 'bootstrap';
  import { fetchEngines } from '../services/engines_service.js';
  import { createImage, createMigrations } from '../services/projects_service.js';
  import FlashAlert from '../components/FlashAlert.svelte';

  export let project = null;

  let modalEl;
  let isGenerating = false;
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

  // Model unificado - usar solo una propiedad para la URL
  let model = {
    content: '',
    image_url: '', // Usar solo esta propiedad para la URL
  };

  // Bandera para controlar si estamos editando
  let isEditing = false;

  // Estado para el flash alert
  let showAlert = false;
  let alertMessage = '';
  let alertType = 'success';

  // Referencia para el input file oculto
  let fileInput;

  // Estado para controlar si el textarea está habilitado
  let isTextareaEnabled = false;

  // Estado de carga para los botones
  let isGeneratingImage = false;

  // Variables para el debounce
  let timeoutId = null;
  let lastContent = '';

  // Variables para el drag and drop
  let isDragging = false;
  let dropZone;

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
      // Resetear estado cuando se abre el modal
      isTextareaEnabled = false;
      model.content = '';
      model.image_url = '';
      lastContent = '';
      isDragging = false;
    });
    
    modalEl.addEventListener('hide.bs.modal', () => {
      isEditing = false;
      isTextareaEnabled = false;
      isDragging = false;
      // Limpiar timeout al cerrar el modal
      if (timeoutId) {
        clearTimeout(timeoutId);
        timeoutId = null;
      }
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
    model.content = '';
    model.image_url = '';
    isTextareaEnabled = false;
    isDragging = false;
    lastContent = '';
    if (timeoutId) {
      clearTimeout(timeoutId);
      timeoutId = null;
    }
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

  async function generateImage() {
    if (!model.content.trim()) {
      showFlashAlert('Primero carga o escribe un modelo PlantUML', 'error');
      return;
    }

    // Evitar generar imagen si el contenido no ha cambiado
    if (model.content === lastContent) {
      return;
    }

    isGeneratingImage = true;
    lastContent = model.content;
    
    try {
      console.log('Enviando modelo al servicio:', model);
      const resp = await createImage(model);
      console.log('Respuesta del servicio:', resp.data);
      
      // Actualizar la propiedad correcta del modelo
      model.image_url = resp.data.url;
    } catch (error) {
      console.error('Error al generar imagen:', error);
      showFlashAlert('Error al generar la imagen', 'error');
    } finally {
      isGeneratingImage = false;
    }
  }

  // Función para manejar cambios en el textarea con debounce
  function handleTextareaChange() {
    if (!isTextareaEnabled || !model.content.trim()) {
      return;
    }

    // Limpiar timeout anterior
    if (timeoutId) {
      clearTimeout(timeoutId);
    }

    // Configurar nuevo timeout (500ms de delay)
    timeoutId = setTimeout(() => {
      generateImage();
      timeoutId = null;
    }, 1000);
  }

  // Función para abrir el selector de archivos
  function openFileSelector() {
    fileInput.click();
  }

  async function generateMigrations (){
    try {
      isGenerating = true;
      console.log('Enviando modelo al servicio:', model);
      
      // Mostrar mensaje de carga
      showFlashAlert('Generando migraciones, por favor espere...', 'info');
      
      const resp = await createMigrations(model.content, project);
      console.log('Respuesta del servicio:', resp.data);
      
      showFlashAlert('Migraciones generadas exitosamente', 'success');
      
    } catch (error) {
      console.error('Error al generar migraciones:', error);
      showFlashAlert('Error al generar las migraciones', 'danger');
    } finally {
      isGenerating = false;
      isGeneratingImage = false;
    }
  }

  // Función para manejar la selección de archivos
  function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Validar que sea un archivo .puml
    if (!file.name.toLowerCase().endsWith('.puml')) {
      showFlashAlert('Por favor, selecciona un archivo con extensión .puml', 'error');
      return;
    }

    processFile(file);

    // Limpiar el input para permitir seleccionar el mismo archivo nuevamente
    event.target.value = '';
  }

  // Función para procesar archivos (compartida para drag and drop y file input)
  function processFile(file) {
    // Leer el contenido del archivo
    const reader = new FileReader();
    reader.onload = function(e) {
      model.content = e.target.result;
      isTextareaEnabled = true; // Habilitar el textarea después de cargar el contenido
      showFlashAlert('Modelo cargado exitosamente. Ahora puedes editar el contenido.', 'success');
      
      // Generar imagen automáticamente después de cargar el archivo
      generateImage();
    };
    reader.onerror = function() {
      showFlashAlert('Error al leer el archivo', 'error');
    };
    reader.readAsText(file);
  }

  // Función para manejar el drag over
  function handleDragOver(event) {
    event.preventDefault();
    if (!isTextareaEnabled) {
      isDragging = true;
    }
  }

  // Función para manejar el drag leave
  function handleDragLeave(event) {
    event.preventDefault();
    isDragging = false;
  }

  // Función para manejar el drop
  function handleDrop(event) {
    event.preventDefault();
    isDragging = false;
    
    if (!isTextareaEnabled) {
      const files = event.dataTransfer.files;
      if (files.length > 0) {
        handleDroppedFile(files[0]);
      }
    }
  }

  // Función para manejar el archivo soltado
  function handleDroppedFile(file) {
    // Validar que sea un archivo .puml
    if (!file.name.toLowerCase().endsWith('.puml')) {
      showFlashAlert('Por favor, suelta un archivo con extensión .puml', 'error');
      return;
    }

    processFile(file);
  }
</script>

<div class="modal fade" tabindex="-1" aria-labelledby="modalLabel" aria-hidden="true" bind:this={modalEl}>
  <div class="modal-dialog modal-fullscreen">
    <div class="modal-content h-100">
        
        <div class="modal-header">
          <h5 class="modal-title" id="modalLabel">Crear Migraciones a Partir de un Modelo de PlantUML</h5>
          
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cerrar" on:click={() => modalInstance.hide()}></button>
        </div>

        <div class="modal-footer">
          <!-- Contenedor flexible para el alert que ocupa el espacio restante -->
          <div class="flex-grow-1 me-3">
            {#if showAlert}
              <FlashAlert 
                message="{alertMessage}"
                type="{alertType}"
                duration={5000}
                position="static"
                on:close={handleAlertClose}
              />
            {/if}
          </div>
          
          <!-- Input file oculto -->
          <input
            type="file"
            bind:this={fileInput}
            accept=".puml"
            style="display: none;"
            on:change={handleFileSelect}
          />
          
          <button 
            type="button" 
            class="btn btn-outline-primary me-2"
            disabled={isGenerating}
            on:click={openFileSelector}>
            <i class="fa fa-search me-2" aria-hidden="true"></i> 
            {#if isGenerating}
              Cargando...
            {:else}
              Seleccionar Modelo
            {/if}
          </button>
          
          <button type="button" 
            class="btn btn-success"
            disabled={isGenerating || model.content == ''}
            on:click={generateMigrations}>
            <i class="fa fa-gear me-2" aria-label="true"></i> 
            {#if isGenerating}
              Generando...
            {:else}
              Generar Migraciones
            {/if}
          </button>
        </div>
        
        <div class="modal-body flex-grow-1" style="min-height: 0;">          
          <div class="row h-100">
            <!-- Columna izquierda: Textarea -->
            <div class="col-md-6 h-100">
              <div class="card h-100">
                <div class="card-header bg-light d-flex justify-content-between align-items-center">
                  <h5 class="card-title mb-0">Modelo de la Base de Datos</h5>
                  <div class="d-flex align-items-center">
                    {#if isGeneratingImage}
                      <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Generando imagen...</span>
                      </div>
                      <small class="text-primary">Actualizando imagen...</small>
                    {:else if isTextareaEnabled}
                      <small class="text-muted">La imagen se actualiza automáticamente</small>
                    {/if}
                  </div>
                </div>
                <div class="card-body p-0 position-relative h-100"
                  bind:this={dropZone}
                  on:dragover={handleDragOver}
                  on:dragleave={handleDragLeave}
                  on:drop={handleDrop}>
                  
                  <textarea
                    class="form-control border-0 h-100"
                    rows="30"
                    bind:value={model.content}
                    placeholder="Luego de seleccionar y cargar un modelo de base de datos de extensión .puml podrá editarlo antes y visualizar el modelo renderizado antes de procesarlo y generar las migraciones"
                    style="resize: none;"
                    disabled={!isTextareaEnabled}
                    on:input={handleTextareaChange}
                  ></textarea>
                  
                  <!-- Overlay cuando está deshabilitado -->
                  {#if !isTextareaEnabled}
                    <div 
                      class="position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center {isDragging ? 'bg-primary bg-opacity-10 border border-primary rounded' : ''}"
                      style="background-color: {isDragging ? 'rgba(13, 110, 253, 0.1)' : 'rgba(248, 249, 250, 0.8)'}; cursor: {isDragging ? 'copy' : 'pointer'}; transition: all 0.2s ease;"
                      on:click={openFileSelector}
                    >
                      <div class="text-center text-muted">
                        {#if isDragging}
                          <i class="fa fa-file-text-o fa-2x mb-2 text-primary"></i>
                          <p class="mb-0 text-primary fw-bold">Suelta el archivo .puml aquí</p>
                        {:else}
                          <i class="fa fa-upload fa-2x mb-2"></i>
                          <p class="mb-0">Selecciona o arrastra un archivo .puml para comenzar</p>
                          <small class="text-muted mt-1">Haz clic en "Seleccionar Modelo" o arrastra y suelta aquí</small>
                        {/if}
                      </div>
                    </div>
                  {/if}
                </div>
              </div>
            </div>

            <!-- Columna derecha: Imagen -->
            <div class="col-md-6 h-100">
              <div class="card h-100">
                <div class="card-header bg-light">
                  <h5 class="card-title mb-0">Imagen del Modelo</h5>
                </div>
                <div
                  class="card-body d-flex flex-column align-items-center justify-content-center p-3 h-100"
                  style="overflow: auto;"
                >
                  {#if model.image_url}
                    <img
                      src={model.image_url}
                      alt="Imagen del modelo PlantUML"
                      class="img-fluid rounded"
                      style="max-height: 100%; max-width: 100%; object-fit: contain;"
                    />
                  {:else}
                    <div class="text-center text-muted">
                      <i class="fa fa-picture-o fa-3x mb-2"></i>
                      <p class="mb-0">La imagen del modelo aparecerá aquí</p>
                      {#if isGeneratingImage}
                        <div class="spinner-border spinner-border-sm mt-2" role="status">
                          <span class="visually-hidden">Generando imagen...</span>
                        </div>
                      {/if}
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          </div>
        </div>
    </div>
  </div>
</div>

<style>
  .modal-fullscreen {
    width: 100vw;
    max-width: none;
    height: 100vh;
    margin: 0;
  }

  .modal-footer{
    padding-bottom: 0px;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.5rem;
    flex-shrink: 0;
  }

  .modal-body{
    padding-top: 8px;
    flex-grow: 1;
    min-height: 0;
  }

  /* Estilos para el textarea deshabilitado */
  textarea:disabled {
    background-color: #f8f9fa;
  }

  /* Asegurar que el modal ocupe toda la pantalla */
  .modal-content {
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  /* Estilos para la zona de drop */
  .drop-zone-active {
    background-color: rgba(13, 110, 253, 0.1) !important;
    border: 2px dashed #0d6efd !important;
  }
</style>