<!-- src/pages/ProjectDetailPage.svelte -->
<script>
  import { createImage } from '../services/projects_service.js';

  export let id; // 👈 Svelte pasará esto automáticamente desde <Route />

  // Datos de ejemplo para el proyecto
  let project = {
    id: id,
    title: "Mi Proyecto",
    description: ``,
    imageUrl: "",
  };

  // Manejar cambios en la descripción
  function handleDescriptionChange(event) {
    project.description = event.target.value;
  }

  // Función para guardar los cambios (simulada)
  function saveProject() {
    //console.log("Guardando proyecto:", project);
    createImage(project).then((resp) => {
      console.log(resp.data);
      project.imageUrl = resp.data.url;
    }).catch((resp) => {
      console.log(resp);
    });
  }
</script>

<svelte:head>
  <title>Editar Proyecto</title>
</svelte:head>

<div class="project w-100">
  <div class="d-flex justify-content-between align-items-center mb-4 px-3">
    <h2 class="h4 fw-bold text-dark mb-0">
      Modelo en PlantUML: {project.title}
    </h2>
    <button class="btn btn-primary" on:click={saveProject}
      ><i class="fa fa-picture-o"></i>Generar Imagen</button
    >
  </div>

  <div class="container-fluid">
    <div class="row">
      <!-- Columna izquierda: Textarea -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-header bg-light">
            <h5 class="card-title mb-0">Descripción del Proyecto</h5>
          </div>
          <div class="card-body p-0">
            <textarea
              class="form-control border-0 h-100"
              rows="40"
              bind:value={project.description}
              placeholder="Escribe aquí la descripción detallada de tu proyecto..."
              style="resize: none; min-height: 600px;"
            ></textarea>
          </div>
        </div>
      </div>

      <!-- Columna derecha: Imagen -->
      <div class="col-md-6">
        <div class="card h-100">
          <div class="card-header bg-light">
            <h5 class="card-title mb-0">Imagen del Proyecto</h5>
          </div>
          <div
            class="card-body d-flex flex-column align-items-center justify-content-center p-3"
          >
            <img
              src={project.imageUrl}
              alt="Imagen del proyecto"
              class="img-fluid rounded mb-3"
              style="max-height: 500px; object-fit: contain;"
            />
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
</style>
