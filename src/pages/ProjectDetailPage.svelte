<!-- src/pages/ProjectDetailPage.svelte -->
<script>
  import { createImage, fetchProject, executeMigrations } from "../services/projects_service.js";
  import { onMount } from "svelte";
  import ModalProjectForm from "../forms/ModalProjectForm.svelte";
  import UploadPUMLForm from "../forms/UploadPUMLForm.svelte";
  import FlashAlert from "../components/FlashAlert.svelte";

  export let id;
  let showAlert = false;
  let alertMessage = "";
  let alertType = "success";
  let modalRef;
  let modalUMLRef;
  let migrations = [];
  let selectedMigration = null;
  let editUp = "";
  let editDown = "";

  onMount(() => {
    fetchProject(id)
      .then((resp) => {
        project = resp.data;
      })
      .catch((resp) => {
        console.log(resp);
      });
  });

  // Datos de ejemplo para el proyecto
  let project = {
    id: id,
    title: "Mi Proyecto",
    description: ``,
    connection_string: "",
    imageUrl: "",
    engine: {
      name: "",
      id: "",
      image: "",
    },
  };

  // Función para generar el nombre de la migración
  function generateMigrationName(migration, timestamp) {
    if (migration.up && migration.up.startsWith('CREATE')) {
      return `${timestamp}_create_${migration.table_name}`;
    }
    return `${timestamp}_migration_${migration.table_name}`;
  }

  // Función para actualizar todos los nombres de las migraciones
  function updateMigrationNames() {
    migrations = migrations.map(migration => {
      return {
        ...migration,
        name: generateMigrationName(migration, migration.timestamp)
      };
    });
  }

  // Mover migración hacia arriba
  function moveUp(index) {
    if (index > 0) {
      // Intercambiar posiciones
      const temp = migrations[index];
      migrations[index] = migrations[index - 1];
      migrations[index - 1] = temp;

      // Intercambiar timestamps
      const tempTimestamp = migrations[index].timestamp;
      migrations[index].timestamp = migrations[index - 1].timestamp;
      migrations[index - 1].timestamp = tempTimestamp;

      // Actualizar los nombres
      updateMigrationNames();
    }
  }

  // Mover migración hacia abajo
  function moveDown(index) {
    if (index < migrations.length - 1) {
      // Intercambiar posiciones
      const temp = migrations[index];
      migrations[index] = migrations[index + 1];
      migrations[index + 1] = temp;

      // Intercambiar timestamps
      const tempTimestamp = migrations[index].timestamp;
      migrations[index].timestamp = migrations[index + 1].timestamp;
      migrations[index + 1].timestamp = tempTimestamp;

      // Actualizar los nombres
      updateMigrationNames();
    }
  }

  // Editar migración
  function editMigration(migration) {
    selectedMigration = migration;
    editUp = migration.up;
    editDown = migration.down;
  }

  // Actualizar migración editada
  function updateMigration() {
    if (selectedMigration) {
      selectedMigration.up = editUp;
      selectedMigration.down = editDown;
      
      // Actualizar el nombre si cambió el tipo de operación
      selectedMigration.name = generateMigrationName(selectedMigration, selectedMigration.timestamp);
      
      // Actualizar la referencia para reactividad
      migrations = migrations;
      selectedMigration = null;
      editUp = "";
      editDown = "";
    }
  }

  // Eliminar migración
  function deleteMigration(index) {
    // Eliminar la migración
    migrations.splice(index, 1);

    // Actualizar la referencia para reactividad
    migrations = migrations;

    // Actualizar nombres después de eliminar
    updateMigrationNames();

    // Limpiar selección si se eliminó la migración seleccionada
    if (selectedMigration && migrations.indexOf(selectedMigration) === -1) {
      selectedMigration = null;
      editUp = "";
      editDown = "";
    }
  }

  // Manejar cambios en la descripción
  function handleDescriptionChange(event) {
    project.description = event.target.value;
  }

  function editProject() {
    modalRef.show();
  }

  function addMigrations() {
    modalUMLRef.show();
  }

  function handleAlertClose() {
    showAlert = false;
    alertMessage = "";
  }

  async function runMigrations() {
    try {
      const resp = await executeMigrations(project, migrations);

      console.log(resp.data);

      if (!resp.data.success) {
        showFlashAlert(
          `${resp.data.message}\n${resp.data.error}`,
          'error'
        );
        return;
      }

      showFlashAlert('Migraciones ejecutadas correctamente', 'success');

    } catch (error) {
      console.error('Error ejecutando migraciones:', error);

      const message = error?.data?.message || 'Error al ejecutar migraciones';
      const detail = error?.data?.error || '';

      showFlashAlert(
        `${message}\n${detail}`,
        'error'
      );
    }
  }

  function showFlashAlert(message, type = "success") {
    alertMessage = message;
    alertType = type;
    showAlert = true;
  }

  function updateMigrationsList(event) {
    var detail = event.detail;
    showFlashAlert(detail.message);

    let counter = 1;
    const baseTimestamp = Date.now();

    function formatSql(sql) {
      let result = '';
      let parenthesisLevel = 0;

      for (let i = 0; i < sql.length; i++) {
        const char = sql[i];

        if (char === '(') {
          parenthesisLevel++;
          result += char;
        } 
        else if (char === ')') {
          parenthesisLevel--;
          result += char;
        } 
        else if (char === ',' && parenthesisLevel === 1) {
          result += ',\n   ';
        } 
        else {
          result += char;
        }
      }

      return result;
    }

    migrations = detail.data.map((json) => {
      const timestamp = baseTimestamp + counter++;

      return {
        ...json,
        up: formatSql(json.up),
        down: formatSql(json.down),
        timestamp,
        name: generateMigrationName(json, timestamp)
      };
    });

    migrations.sort((a, b) => a.timestamp - b.timestamp);
  }
</script>

<svelte:head>
  <title>Editar Proyecto</title>
</svelte:head>

<ModalProjectForm bind:this={modalRef} showContinue={false} {project} />

<UploadPUMLForm
  bind:this={modalUMLRef}
  {project}
  on:refreshList={(e) => updateMigrationsList(e)}
/>

<div class="project w-100">
  {#if showAlert}
    <div class="px-3">
      <FlashAlert
        message={alertMessage}
        type={alertType}
        duration={5000}
        position="absolute"
        on:close={handleAlertClose}
      />
    </div>
  {/if}

  <div class="d-flex justify-content-between align-items-center mb-4 px-3">
    <h2 class="h4 fw-bold text-dark mb-0">
      Modelo en PlantUML: {project.title}
    </h2>
    <div>
      <button class="btn btn-primary" on:click={editProject}>
        <i class="fa fa-pencil"></i>Editar Proyecto
      </button>
      <button class="btn btn-primary" on:click={addMigrations}>
        <i class="fa fa-plus"></i>Agregar Migraciones
      </button>
      <button class="btn btn-success" on:click={runMigrations}>
        <i class="fa fa-check"></i>Ejecutar Migraciones
      </button>
    </div>
  </div>

  <div class="container-fluid">
    <div class="row">
      <!-- Primera columna: Tabla de migraciones -->
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h5 class="card-title mb-0">Migraciones</h5>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-striped table-hover mb-0">
                <thead>
                  <tr>
                    <th>Nombre</th>
                    <th>Operaciones</th>
                  </tr>
                </thead>
                <tbody>
                  {#if migrations.length > 0}
                    {#each migrations as migration, index}
                      <tr>
                        <td class="fw-bold">{migration.name}</td>
                        <td>
                          <div class="btn-group btn-group-sm" role="group">
                            <!-- Flecha arriba -->
                            <button
                              class="btn btn-outline-secondary"
                              on:click={() => moveUp(index)}
                              disabled={index === 0}
                              title="Mover arriba"
                            >
                              <i class="fa fa-arrow-up"></i>
                            </button>

                            <!-- Flecha abajo -->
                            <button
                              class="btn btn-outline-secondary"
                              on:click={() => moveDown(index)}
                              disabled={index === migrations.length - 1}
                              title="Mover abajo"
                            >
                              <i class="fa fa-arrow-down"></i>
                            </button>

                            <!-- Editar -->
                            <button
                              class="btn btn-outline-primary"
                              on:click={() => editMigration(migration)}
                              title="Editar migración"
                            >
                              <i class="fa fa-pencil"></i>
                            </button>

                            <!-- Eliminar -->
                            <button
                              class="btn btn-outline-danger"
                              on:click={() => deleteMigration(index)}
                              title="Eliminar migración"
                            >
                              <i class="fa fa-times"></i>
                            </button>
                          </div>
                        </td>
                      </tr>
                    {/each}
                  {:else}
                    <tr>
                      <td colspan="2" class="text-center text-muted py-3">
                        No hay migraciones disponibles
                      </td>
                    </tr>
                  {/if}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Segunda columna: Detalles de la migración -->
      <div class="col-md-6">
        <div class="card">
          <div class="card-header">
            <h5 class="card-title mb-0">
              {#if selectedMigration}
                Editando: {selectedMigration.name}
              {:else}
                Detalles del Proyecto
              {/if}
            </h5>
          </div>
          <div class="card-body">
            {#if selectedMigration}
              <!-- Formulario de edición -->
              <div class="mb-3">
                <label class="form-label fw-bold"
                  >UP (Creación/Modificación):</label
                >
                <textarea
                  class="form-control"
                  rows="6"
                  bind:value={editUp}
                  placeholder="SQL para crear o modificar la tabla..."
                ></textarea>
              </div>

              <div class="mb-3">
                <label class="form-label fw-bold">DOWN (Reversión):</label>
                <textarea
                  class="form-control"
                  rows="4"
                  bind:value={editDown}
                  placeholder="SQL para revertir los cambios..."
                ></textarea>
              </div>

              <div class="d-flex gap-2">
                <button class="btn btn-success" on:click={updateMigration}>
                  <i class="fa fa-check"></i> Actualizar Migración
                </button>
                <button
                  class="btn btn-secondary"
                  on:click={() => {
                    selectedMigration = null;
                    editUp = "";
                    editDown = "";
                  }}
                >
                  <i class="fa fa-times"></i> Cancelar
                </button>
              </div>
            {:else}
              <!-- Vista normal de detalles del proyecto -->
              <div class="mb-4">
                <div class="d-flex align-items-start justify-content-between mb-3">
                  <div class="flex-grow-1 me-3">
                    <!-- Información básica del proyecto -->
                    <p class="mb-2"><strong>Título:</strong> {project.title}</p>
                    <p class="mb-2"><strong>Motor:</strong> {project.engine.name}</p>
                    <p class="mb-2"><strong>Cadena de Conexión:</strong> <br>{project.connection_string}</p>
                  </div>
                </div>
                
                <!-- Descripción en fila separada -->
                <div class="row">
                  <div class="col-12">
                    <p class="mb-2"><strong>Descripción:</strong></p>
                    <textarea 
                      class="form-control" 
                      rows="4"
                      value={project.description}
                      disabled
                      on:input={handleDescriptionChange}
                      placeholder="Agrega una descripción para tu proyecto..."
                    ></textarea>
                  </div>
                </div>
              </div>

              {#if migrations.length > 0}
                <div class="mt-3">
                  <p>
                    <strong>Total de migraciones:</strong>
                    {migrations.length}
                  </p>
                  <p class="text-muted small">
                    Selecciona una migración de la lista para editarla
                  </p>
                </div>
              {/if}
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .project {
    width: 100%;
    margin-bottom: 50px;
    padding-top: 10px;
  }

  textarea:focus {
    outline: none;
    box-shadow: none;
  }

  .card {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
    border: 1px solid rgba(0, 0, 0, 0.125);
  }

  .table th {
    border-top: none;
    font-weight: 600;
    background-color: #f8f9fa;
  }

  .badge {
    font-size: 0.75em;
  }

  .btn-group .btn {
    padding: 0.25rem 0.5rem;
  }

  .form-label {
    font-size: 0.9rem;
  }
</style>