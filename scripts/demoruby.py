# uml_to_sinatra.py
import re
import os
import json
from pathlib import Path
from langchain_ollama import ChatOllama
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

class PlantUMLToSinatra:
    def __init__(self, model="llama3.2"):
        self.llm = ChatOllama(model=model)
        self.template_dir = "sinatra_templates"
        
    def parse_plantuml(self, plantuml_code):
        """Extrae entidades y relaciones del código PlantUML"""
        # Analizar clases y atributos
        classes = {}
        class_pattern = r'class\s+(\w+)\s*\{([^}]*)\}'
        for match in re.finditer(class_pattern, plantuml_code, re.DOTALL):
            class_name = match.group(1)
            attributes = re.findall(r'\s*(\w+)\s*:\s*(\w+)', match.group(2))
            classes[class_name] = attributes
        
        # Analizar relaciones
        relationships = []
        rel_pattern = r'(\w+)\s*([<|]?[-.]+[>|]?)\s*(\w+)'
        for match in re.finditer(rel_pattern, plantuml_code):
            from_class, rel_type, to_class = match.groups()
            relationships.append({
                'from': from_class,
                'to': to_class,
                'type': rel_type
            })
        
        return {
            'classes': classes,
            'relationships': relationships
        }
    
    def generate_sinatra_app(self, uml_data):
        """Genera la aplicación Sinatra completa"""
        
        # Prompt para generar el código MVC
        prompt_template = """
Eres un experto en Ruby y Sinatra. Basándote en el siguiente diagrama UML:

{uml_data}

Genera una aplicación Sinatra MVC completa con:

1. Modelos ActiveRecord con validaciones
2. Controladores Sinatra con rutas RESTful
3. Vistas ERB con formularios
4. Migraciones de base de datos
5. Configuración completa

Usa esta estructura de plantilla:

app/
├── models/
├── controllers/
├── views/
├── migrations/
config/
├── database.yml
config.ru
Gemfile

Devuelve SOLO el código Ruby/ERB necesario, sin explicaciones.
"""
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        chain = prompt | self.llm | StrOutputParser()
        
        return chain.invoke({"uml_data": json.dumps(uml_data, indent=2)})
    
    def create_project_structure(self, generated_code, output_dir="generated_app"):
        """Crea la estructura de archivos del proyecto"""
        
        # Patrones para extraer diferentes tipos de archivos
        patterns = {
            'models': r'# MODEL: (\w+\.rb)\n(.*?)(?=# MODEL|\Z)',
            'controllers': r'# CONTROLLER: (\w+\.rb)\n(.*?)(?=# CONTROLLER|\Z)',
            'views': r'# VIEW: ([\w/]+\.erb)\n(.*?)(?=# VIEW|\Z)',
            'migrations': r'# MIGRATION: (\d+_\w+\.rb)\n(.*?)(?=# MIGRATION|\Z)',
            'config': r'# CONFIG: (\w+\.\w+)\n(.*?)(?=# CONFIG|\Z)'
        }
        
        # Crear directorios
        base_dir = Path(output_dir)
        directories = ['app/models', 'app/controllers', 'app/views', 
                      'db/migrate', 'config']
        
        for dir_path in directories:
            (base_dir / dir_path).mkdir(parents=True, exist_ok=True)
        
        # Extraer y guardar archivos
        for category, pattern in patterns.items():
            matches = re.findall(pattern, generated_code, re.DOTALL)
            for filename, content in matches:
                if category == 'views':
                    # Las vistas pueden tener subdirectorios
                    file_path = base_dir / 'app' / 'views' / filename
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                elif category == 'migrations':
                    file_path = base_dir / 'db' / 'migrate' / filename
                elif category == 'config':
                    file_path = base_dir / 'config' / filename
                else:
                    file_path = base_dir / 'app' / category / filename
                
                file_path.write_text(content.strip())
        
        # Crear archivos básicos si no se generaron
        self._create_default_files(base_dir)
    
    def _create_default_files(self, base_dir):
        """Crea archivos por defecto si no están en la generación"""
        
        # Gemfile por defecto
        gemfile = base_dir / "Gemfile"
        if not gemfile.exists():
            gemfile.write_text("""
source 'https://rubygems.org'

gem 'sinatra'
gem 'sinatra-activerecord'
gem 'sqlite3'
gem 'rake'
gem 'require_all'
            """)
        
        # config.ru por defecto
        config_ru = base_dir / "config.ru"
        if not config_ru.exists():
            config_ru.write_text("""
require './app/controllers/application_controller'
run Sinatra::Application
            """)
        
        # database.yml por defecto
        database_yml = base_dir / "config" / "database.yml"
        if not database_yml.exists():
            database_yml.write_text("""
development:
  adapter: sqlite3
  database: db/development.sqlite3
  pool: 5
  timeout: 5000
            """)

# --- USO ---
def main():
    # Código PlantUML de ejemplo
    plantuml_code = """
@startuml
class User {
  id: integer
  name: string
  email: string
  created_at: datetime
}

class Post {
  id: integer
  title: string
  content: text
  user_id: integer
  created_at: datetime
}

User ||--o{ Post : has_many
@enduml
"""
    
    # Procesar
    converter = PlantUMLToSinatra()
    uml_data = converter.parse_plantuml(plantuml_code)
    sinatra_code = converter.generate_sinatra_app(uml_data)
    
    # Guardar y crear estructura
    converter.create_project_structure(sinatra_code, "my_sinatra_app")
    print("✅ Aplicación Sinatra generada en 'my_sinatra_app/'")

if __name__ == "__main__":
    main()