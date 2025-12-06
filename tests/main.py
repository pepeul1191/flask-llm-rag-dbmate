from test_ollama import measuring

# Ejecutar todas las pruebas
def run_all_tests():
  print("Ejecutando todas las pruebas...")
  measuring('ollama_basico', 'sqlite', 'basico.puml')
  measuring('ollama_basico', 'postgres', 'basico.puml')
  measuring('ollama_basico', 'mysql', 'basico.puml')
  print("Todas las pruebas completadas.")

if __name__ == "__main__":
    run_all_tests()