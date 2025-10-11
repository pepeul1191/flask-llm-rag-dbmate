<script>
  import { onMount } from 'svelte';
  import { navigate } from 'svelte-routing';
  //import { goTo } from '../components/NavBar.svelte';
  
  // Estado del slider
  let currentSlide = 0;
  let slides = [
    {
      id: 1,
      title: "Versionado Inteligente de Bases de Datos",
      description: "Combina MDE y LLMs para automatizar el versionado y evolución de tus esquemas de base de datos relacionales",
      image: "https://images.unsplash.com/photo-1558494949-ef010cbdcc31?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      buttonText: "Comenzar Demo",
      buttonLink: "#demo"
    },
    {
      id: 2,
      title: "Ingeniería Dirigida por Modelos",
      description: "Transforma tus modelos conceptuales en código SQL versionado automáticamente",
      image: "https://images.unsplash.com/photo-1635070041078-e363dbe005cb?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      buttonText: "Ver Ejemplos",
      buttonLink: "#examples"
    },
    {
      id: 3,
      title: "LLMs para Generación de Migraciones",
      description: "Inteligencia artificial que entende tu contexto y genera migraciones SQL seguras",
      image: "https://images.unsplash.com/photo-1677442136019-21780ecad995?ixlib=rb-4.0.3&auto=format&fit=crop&w=2000&q=80",
      buttonText: "Probar Ahora",
      buttonLink: "#try"
    }
  ];

  // Características principales
  const features = [
    {
      icon: "🔄",
      title: "Versionado Automático",
      description: "Control automático de versiones de esquema con historial completo de cambios"
    },
    {
      icon: "🤖",
      title: "LLM Integration",
      description: "Generación inteligente de SQL usando modelos de lenguaje avanzados"
    },
    {
      icon: "📊",
      title: "Model-Driven Engineering",
      description: "De modelos conceptuales a código SQL ejecutable automáticamente"
    },
    {
      icon: "⚡",
      title: "Migraciones Seguras",
      description: "Generación y validación de migraciones SQL con rollback automático"
    },
    {
      icon: "🔍",
      title: "Análisis de Impacto",
      description: "Detección automática de impactos en cambios de esquema"
    },
    {
      icon: "📝",
      title: "Documentación Auto-generada",
      description: "Documentación técnica siempre actualizada basada en tus modelos"
    }
  ];

  // Función para cambiar slide
  function nextSlide() {
    currentSlide = (currentSlide + 1) % slides.length;
  }

  function prevSlide() {
    currentSlide = (currentSlide - 1 + slides.length) % slides.length;
  }

  function goToSlide(index) {
    currentSlide = index;
  }

  function goToProjects() {
    navigate('/projects');
  }

  // Auto-play del slider
  onMount(() => {
    const interval = setInterval(() => {
      nextSlide();
    }, 5000);

    return () => clearInterval(interval);
  });
</script>

<svelte:head>
  <title>MDE LLM SQL Generator</title>
</svelte:head>

<!-- Hero Slider -->
<section class="hero-slider" id="home">
  <div class="slider-container">
    {#each slides as slide, index}
      <div class="slide {index === currentSlide ? 'active' : ''}" 
           style="background-image: url('{slide.image}')">
        <div class="slide-content">
          <h1>{slide.title}</h1>
          <p>{slide.description}</p>
        </div>
      </div>
    {/each}
  </div>

  <!-- Controles del slider -->
  <button class="slider-control prev" on:click={prevSlide}>‹</button>
  <button class="slider-control next" on:click={nextSlide}>›</button>

  <!-- Indicadores -->
  <div class="slider-indicators">
    {#each slides as _, index}
      <button 
        class="indicator {index === currentSlide ? 'active' : ''}" 
        on:click={() => goToSlide(index)}
      >
        ●
      </button>
    {/each}
  </div>
</section>

<!-- Sección de problema/solución -->
<section class="problem-solution">
  <div class="section-container">
    <div class="problem-column">
      <h2>El Problema</h2>
      <div class="problem-list">
        <div class="problem-item">
          <span class="problem-icon">❌</span>
          <div>
            <h4>Versionado Manual de BD</h4>
            <p>Scripts SQL desorganizados y difíciles de mantener</p>
          </div>
        </div>
        <div class="problem-item">
          <span class="problem-icon">❌</span>
          <div>
            <h4>Migraciones Peligrosas</h4>
            <p>Errores humanos en scripts de migración crítica</p>
          </div>
        </div>
        <div class="problem-item">
          <span class="problem-icon">❌</span>
          <div>
            <h4>Documentación Desactualizada</h4>
            <p>Esquemas de BD sin documentación consistente</p>
          </div>
        </div>
      </div>
    </div>
    
    <div class="solution-column">
      <h2>Nuestra Solución</h2>
      <div class="solution-list">
        <div class="solution-item">
          <span class="solution-icon">✅</span>
          <div>
            <h4>Versionado Automatizado</h4>
            <p>Control automático de versiones con MDE</p>
          </div>
        </div>
        <div class="solution-item">
          <span class="solution-icon">✅</span>
          <div>
            <h4>Migraciones Inteligentes</h4>
            <p>LLMs generan SQL seguro y optimizado</p>
          </div>
        </div>
        <div class="solution-item">
          <span class="solution-icon">✅</span>
          <div>
            <h4>Documentación en Tiempo Real</h4>
            <p>Documentación auto-generada desde los modelos</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- Sección de características -->
<section class="features" id="features">
  <div class="section-container">
    <h2>Características Principales</h2>
    <p class="section-subtitle">Potenciado por MDE y LLMs para un versionado de bases de datos inteligente</p>
    
    <div class="features-grid">
      {#each features as feature}
        <div class="feature-card">
          <div class="feature-icon">{feature.icon}</div>
          <h3>{feature.title}</h3>
          <p>{feature.description}</p>
        </div>
      {/each}
    </div>
  </div>
</section>

<!-- Sección de flujo de trabajo -->
<section class="workflow">
  <div class="section-container">
    <h2>Flujo de Trabajo Inteligente</h2>
    <div class="workflow-steps">
      <div class="workflow-step">
        <div class="step-number">1</div>
        <h4>Modelado Conceptual</h4>
        <p>Define tus modelos de datos usando MDE</p>
      </div>
      <div class="workflow-step">
        <div class="step-number">2</div>
        <h4>Generación con LLMs</h4>
        <p>Nuestros modelos generan SQL optimizado</p>
      </div>
      <div class="workflow-step">
        <div class="step-number">3</div>
        <h4>Versionado Automático</h4>
        <p>Control automático de versiones de esquema</p>
      </div>
      <div class="workflow-step">
        <div class="step-number">4</div>
        <h4>Migraciones Seguras</h4>
        <p>Despliegue seguro con rollback automático</p>
      </div>
    </div>
  </div>
</section>

<!-- Sección CTA -->
<section class="cta-section" id="demo">
  <div class="section-container">
    <h2>¿Listo para Revolucionar tu Versionado de BD?</h2>
    <p>Comienza a usar MDE y LLMs para un control de bases de datos inteligente y seguro</p>
    <div class="cta-buttons">
      <button class="cta-primary" on:click={goToProjects}>Crea tu Primer Proyecto</button>
      <a href="/docs/manual-usuario.pdf" target="_blank" class="btn btn-outline-light btn-lg px-5 py-3 fw-bold cta-secondary">
        Ver Documentación
      </a>
    </div>
    <div class="tech-stack">
      <span>Tecnologías: </span>
      <span class="tech-tag">MDE</span>
      <span class="tech-tag">LLMs</span>
      <span class="tech-tag">SQL</span>
      <span class="tech-tag">Git</span>
      <span class="tech-tag">CI/CD</span>
    </div>
  </div>
</section>

<style>
  /* Reset y estilos base */
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: 'Arial', sans-serif;
    line-height: 1.6;
    color: #2c3e50;
  }

  /* Hero Slider */
  .hero-slider {
    position: relative;
    height: 100vh;
    overflow: hidden;
  }

  .slider-container {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .slide {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    opacity: 0;
    transition: opacity 0.8s ease-in-out;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .slide.active {
    opacity: 1;
  }

  .slide-content {
    text-align: center;
    color: white;
    background: rgba(0, 0, 0, 0.7);
    padding: 3rem;
    border-radius: 15px;
    max-width: 800px;
    backdrop-filter: blur(10px);
  }

  .slide-content h1 {
    font-size: 3rem;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  }

  .slide-content p {
    font-size: 1.3rem;
    margin-bottom: 2rem;
    line-height: 1.6;
  }

  .cta-button {
    display: inline-block;
    background: #3498db;
    color: white;
    padding: 15px 35px;
    text-decoration: none;
    border-radius: 8px;
    font-weight: bold;
    font-size: 1.1rem;
    transition: all 0.3s;
    border: none;
    cursor: pointer;
  }

  .cta-button:hover {
    background: #2980b9;
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  }

  /* Controles del slider */
  .slider-control {
    position: absolute;
    top: 50%;
    transform: translateY(-50%);
    background: rgba(255, 255, 255, 0.9);
    border: none;
    width: 60px;
    height: 60px;
    border-radius: 50%;
    font-size: 2rem;
    cursor: pointer;
    transition: all 0.3s;
    z-index: 10;
    color: #2c3e50;
  }

  .slider-control:hover {
    background: white;
    transform: translateY(-50%) scale(1.1);
  }

  .prev {
    left: 2rem;
  }

  .next {
    right: 2rem;
  }

  /* Indicadores */
  .slider-indicators {
    position: absolute;
    bottom: 2rem;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    gap: 0.5rem;
  }

  .indicator {
    background: rgba(255, 255, 255, 0.5);
    border: none;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    cursor: pointer;
    font-size: 0;
    transition: all 0.3s;
  }

  .indicator.active {
    background: white;
    transform: scale(1.2);
  }

  /* Sección Problema/Solución */
  .problem-solution {
    background: #f8f9fa;
    padding: 4rem 0;
  }

  .section-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
  }

  .problem-solution .section-container {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 4rem;
    align-items: start;
  }

  .problem-column h2, .solution-column h2 {
    font-size: 2rem;
    margin-bottom: 2rem;
    color: #2c3e50;
  }

  .problem-item, .solution-item {
    display: flex;
    align-items: start;
    gap: 1rem;
    margin-bottom: 2rem;
    padding: 1.5rem;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  }

  .problem-icon, .solution-icon {
    font-size: 1.5rem;
    flex-shrink: 0;
  }

  .problem-item h4, .solution-item h4 {
    color: #2c3e50;
    margin-bottom: 0.5rem;
  }

  .problem-item {
    border-left: 4px solid #e74c3c;
  }

  .solution-item {
    border-left: 4px solid #27ae60;
  }

  /* Sección de características */
  .features {
    padding: 6rem 0;
    background: white;
  }

  .features h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 1rem;
    color: #2c3e50;
  }

  .section-subtitle {
    text-align: center;
    font-size: 1.2rem;
    color: #7f8c8d;
    margin-bottom: 4rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
    gap: 2rem;
  }

  .feature-card {
    background: white;
    padding: 2.5rem 2rem;
    border-radius: 12px;
    text-align: center;
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
    border: 1px solid #e9ecef;
  }

  .feature-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.15);
  }

  .feature-icon {
    font-size: 3.5rem;
    margin-bottom: 1.5rem;
  }

  .feature-card h3 {
    font-size: 1.5rem;
    margin-bottom: 1rem;
    color: #2c3e50;
  }

  .feature-card p {
    color: #7f8c8d;
    line-height: 1.6;
  }

  /* Flujo de trabajo */
  .workflow {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 6rem 0;
  }

  .workflow h2 {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 4rem;
  }

  .workflow-steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 2rem;
  }

  .workflow-step {
    text-align: center;
    padding: 2rem;
  }

  .step-number {
    width: 60px;
    height: 60px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    font-weight: bold;
    margin: 0 auto 1.5rem;
    backdrop-filter: blur(10px);
  }

  .workflow-step h4 {
    font-size: 1.3rem;
    margin-bottom: 1rem;
  }

  /* CTA Section */
  .cta-section {
    background: #2c3e50;
    color: white;
    padding: 6rem 0;
    text-align: center;
  }

  .cta-section h2 {
    font-size: 2.5rem;
    margin-bottom: 1rem;
  }

  .cta-section p {
    font-size: 1.2rem;
    margin-bottom: 3rem;
    opacity: 0.9;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
  }

  .cta-buttons {
    display: flex;
    gap: 1rem;
    justify-content: center;
    margin-bottom: 3rem;
    flex-wrap: wrap;
  }

  .cta-primary, .cta-secondary {
    padding: 15px 35px;
    border: none;
    border-radius: 8px;
    font-size: 1.1rem;
    cursor: pointer;
    transition: all 0.3s;
    font-weight: bold;
  }

  .cta-primary {
    background: #3498db;
    color: white;
  }

  .cta-secondary {
    background: transparent;
    color: white;
    border: 2px solid white;
  }

  .cta-primary:hover, .cta-secondary:hover {
    transform: translateY(-2px);
    box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
  }

  .tech-stack {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .tech-tag {
    background: rgba(255, 255, 255, 0.1);
    padding: 0.5rem 1rem;
    border-radius: 20px;
    font-size: 0.9rem;
  }

  /* Responsive */
  @media (max-width: 768px) {
    .slide-content h1 {
      font-size: 2rem;
    }
    
    .slide-content p {
      font-size: 1rem;
    }
    
    .problem-solution .section-container {
      grid-template-columns: 1fr;
      gap: 2rem;
    }
    
    .slider-control {
      width: 50px;
      height: 50px;
      font-size: 1.5rem;
    }
    
    .prev {
      left: 1rem;
    }
    
    .next {
      right: 1rem;
    }
    
    .features-grid {
      grid-template-columns: 1fr;
    }
    
    .workflow-steps {
      grid-template-columns: 1fr;
    }
    
    .cta-buttons {
      flex-direction: column;
      align-items: center;
    }
    
    .cta-primary, .cta-secondary {
      width: 100%;
      max-width: 300px;
    }
  }
</style>