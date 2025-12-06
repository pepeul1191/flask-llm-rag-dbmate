from test_ollama import measuring as ollama_measuring
from test_qwen import measuring as qwen_measuring
from test_deepseek import measuring as deepseek_measuring
from test_bert import measuring as bert_measuring

# Ejecutar todas las pruebas
def run_all_tests():
  print("Ejecutando todas las pruebas...")
  #ollama_measuring('ollama_basico', 'sqlite', 'basico.puml')
  #ollama_measuring('ollama_basico', 'postgres', 'basico.puml')
  #ollama_measuring('ollama_basico', 'mysql', 'basico.puml')
  #qwen_measuring('qwen_basico', 'sqlite', 'basico.puml')
  #qwen_measuring('qwen_basico', 'postgres', 'basico.puml')
  #qwen_measuring('qwen_basico', 'mysql', 'basico.puml')
  #deepseek_measuring('deepseek_basico', 'sqlite', 'basico.puml')
  #deepseek_measuring('deepseek_basico', 'postgres', 'basico.puml')
  #deepseek_measuring('deepseek_basico', 'mysql', 'basico.puml')
  bert_measuring('bert_basico', 'sqlite', 'basico.puml')
  bert_measuring('bert_basico', 'postgres', 'basico.puml')
  bert_measuring('bert_basico', 'mysql', 'basico.puml')
  print("Todas las pruebas completadas.")

if __name__ == "__main__":
    run_all_tests()