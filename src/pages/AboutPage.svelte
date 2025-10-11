<script>
</script>

<svelte:head>
  <title>Acerca del Desarrollador</title>
</svelte:head>

<div class="container py-5">
  <div class="row justify-content-center">
    <div class="col-lg-10">
      <!-- Header -->
      <div class="text-center mb-5">
        <h1 class="display-4 fw-bold text-dark mb-3">Acerca del Autor</h1>
        <div class="border-bottom border-primary border-3 mx-auto" style="width: 100px;"></div>
      </div>

      <!-- Contenido principal -->
      <div class="row align-items-start g-5">
        <!-- Columna de la foto -->
        <div class="col-md-4 text-center">
          <div class="profile-card p-4 bg-light rounded-3 shadow-sm">
            <img 
              src="/img/pepis.png" 
              alt="José Jesús Valdivia Caballero"
              class="img-fluid rounded-circle mb-4 shadow"
              style="width: 250px; height: 250px; object-fit: cover;"
            />
            <h3 class="fw-bold text-dark mb-2">José Jesús Valdivia Caballero</h3>
            <p class="text-muted mb-3">Ingeniero de Sistemas | Magíster | Doctorando</p>
            
            <!-- Badges de especialización -->
            <div class="d-flex flex-wrap justify-content-center gap-2">
              <span class="badge bg-primary">Ingeniería de Software</span>
              <span class="badge bg-success">Inteligencia Artificial</span>
              <span class="badge bg-info">Emprendimiento</span>
            </div>
          </div>
        </div>

        <!-- Columna de la descripción -->
        <div class="col-md-8">
          <div class="description-card p-4 bg-white rounded-3 shadow-sm h-100">
            <!-- Formación académica -->
            <div class="mb-4">
              <h4 class="fw-bold text-primary mb-3">
                <i class="fa fa-graduation-cap me-2"></i>Formación Académica
              </h4>
              <div class="timeline">
                <div class="timeline-item mb-3">
                  <div class="d-flex">
                    <div class="timeline-badge bg-primary rounded-circle me-3 d-flex align-items-center justify-content-center" 
                         style="width: 40px; height: 40px;">
                      <i class="fa fa-university text-white"></i>
                    </div>
                    <div>
                      <h6 class="fw-bold mb-1">Doctorado en Ingeniería de Sistemas</h6>
                      <p class="text-muted mb-1">Universidad Nacional Mayor de San Marcos</p>
                      <small class="text-muted">En curso</small>
                    </div>
                  </div>
                </div>
                
                <div class="timeline-item mb-3">
                  <div class="d-flex">
                    <div class="timeline-badge bg-success rounded-circle me-3 d-flex align-items-center justify-content-center" 
                         style="width: 40px; height: 40px;">
                      <i class="fa fa-mortar-board text-white"></i>
                    </div>
                    <div>
                      <h6 class="fw-bold mb-1">Magíster en Ingeniería de Sistemas</h6>
                      <p class="text-muted mb-1">Universidad Nacional Mayor de San Marcos</p>
                      <small class="text-muted">Concluido</small>
                    </div>
                  </div>
                </div>
                
                <div class="timeline-item">
                  <div class="d-flex">
                    <div class="timeline-badge bg-info rounded-circle me-3 d-flex align-items-center justify-content-center" 
                         style="width: 40px; height: 40px;">
                      <i class="fa fa-book text-white"></i>
                    </div>
                    <div>
                      <h6 class="fw-bold mb-1">Ingeniero de Sistemas</h6>
                      <p class="text-muted mb-1">Universidad de Lima</p>
                      <small class="text-muted">Concluido</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Experiencia profesional -->
            <div class="mb-4">
              <h4 class="fw-bold text-primary mb-3">
                <i class="fa fa-briefcase me-2"></i>Experiencia Profesional
              </h4>
              <p class="mb-3">
                Cuenta con experiencia en el desarrollo de software web y móvil en entornos 
                empresariales y en el ámbito de la educación superior.
              </p>
              <div class="row">
                <div class="col-sm-6 mb-2">
                  <div class="d-flex align-items-center">
                    <i class="fa fa-check-circle text-success me-2"></i>
                    <span>Desarrollo de software web y móvil</span>
                  </div>
                </div>
                <div class="col-sm-6 mb-2">
                  <div class="d-flex align-items-center">
                    <i class="fa fa-check-circle text-success me-2"></i>
                    <span>Entornos empresariales</span>
                  </div>
                </div>
                <div class="col-sm-6 mb-2">
                  <div class="d-flex align-items-center">
                    <i class="fa fa-check-circle text-success me-2"></i>
                    <span>Ámbito de educación superior</span>
                  </div>
                </div>
                <div class="col-sm-6 mb-2">
                  <div class="d-flex align-items-center">
                    <i class="fa fa-check-circle text-success me-2"></i>
                    <span>Liderazgo de equipos de desarrollo</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Liderazgo y metodologías -->
            <div class="mb-4">
              <h4 class="fw-bold text-primary mb-3">
                <i class="fa fa-users me-2"></i>Liderazgo y Metodologías
              </h4>
              <p class="mb-3">
                Ha liderado, gestionado y empoderado equipos de desarrollo bajo enfoques 
                de metodologías ágiles, promoviendo la colaboración y la excelencia técnica.
              </p>
              <div class="d-flex flex-wrap gap-2">
                <span class="badge bg-warning text-dark">Metodologías Ágiles</span>
                <span class="badge bg-secondary">Liderazgo de Equipos</span>
                <span class="badge bg-dark">Gestión de Proyectos</span>
                <span class="badge bg-success">Empowerment</span>
              </div>
            </div>

            <!-- Áreas de interés -->
            <div>
              <h4 class="fw-bold text-primary mb-3">
                <i class="fa fa-star me-2"></i>Áreas de Interés
              </h4>
              <div class="row g-3">
                <div class="col-sm-4">
                  <div class="text-center p-3 bg-primary bg-opacity-10 rounded-3">
                    <i class="fa fa-code text-primary fa-2x mb-2"></i>
                    <h6 class="fw-bold">Ingeniería de Software</h6>
                  </div>
                </div>
                <div class="col-sm-4">
                  <div class="text-center p-3 bg-success bg-opacity-10 rounded-3">
                    <i class="fa fa-cogs text-success fa-2x mb-2"></i>
                    <h6 class="fw-bold">Inteligencia Artificial</h6>
                  </div>
                </div>
                <div class="col-sm-4">
                  <div class="text-center p-3 bg-info bg-opacity-10 rounded-3">
                    <i class="fa fa-lightbulb-o text-info fa-2x mb-2"></i>
                    <h6 class="fw-bold">Emprendimiento</h6>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Sección de contacto adicional -->
      <div class="row mt-5">
        <div class="col-12">
          <div class="bg-light rounded-3 p-4 text-center">
            <h5 class="fw-bold mb-3">¿Interesado en colaborar?</h5>
            <div class="d-flex flex-wrap justify-content-center gap-3">
              <a href="mailto:pepe.valdivia.caballero@gmail.com" class="btn btn-primary">
                <i class="fa fa-envelope me-2"></i>Contactar por Email
              </a>
              <a href="https://pe.linkedin.com/in/jos%C3%A9-valdivia-caballero-b99a12138" target="_blank" class="btn btn-outline-dark">
                <i class="fa fa-linkedin me-2"></i>LinkedIn
              </a>
              <a href="https://github.com/pepeul1191" target="_blank" class="btn btn-success">
                <i class="fa fa-github me-2"></i>GitHub
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .profile-card, .description-card {
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }
  
  .profile-card:hover, .description-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.1) !important;
  }
  
  .timeline-item {
    position: relative;
  }
  
  .timeline-item:not(:last-child):after {
    content: '';
    position: absolute;
    left: 20px;
    top: 40px;
    bottom: -20px;
    width: 2px;
    background: #e9ecef;
  }
  
  .badge {
    font-size: 0.75rem;
    padding: 0.5em 0.75em;
  }
  
  .fa-2x {
    font-size: 2em;
  }
</style>
