from test_ollama import measuring as ollama_measuring
from test_ollama_tiny import measuring as ollama_tiny_measuring
from test_qwen import measuring as qwen_measuring
from test_qwen_tiny import measuring as qwen_tiny_measuring
from test_deepseek import measuring as deepseek_measuring
from test_deepseek_tiny import measuring as deepseek_tiny_measuring
from test_gemma import measuring as gemma_measuring
from test_gemma_tiny import measuring as gemma_tiny_measuring
from test_mistral import measuring as mistral_measuring
from test_bert import measuring as bert_measuring

# Ejecutar todas las pruebas
def run_all_tests():
  print("Ejecutando todas las pruebas...")

  ollama_measuring('llama3.2:3b', 'sqlite', 'basico.puml')
  ollama_measuring('llama3.2:3b', 'postgres', 'basico.puml')
  ollama_measuring('llama3.2:3b', 'mysql', 'basico.puml')

  ollama_tiny_measuring('tinyllama:1.1b', 'sqlite', 'basico.puml')
  ollama_tiny_measuring('tinyllama:1.1b', 'postgres', 'basico.puml')
  ollama_tiny_measuring('tinyllama:1.1b', 'mysql', 'basico.puml')

  qwen_measuring('qwen2.5:7b', 'sqlite', 'basico.puml')
  qwen_measuring('qwen2.5:7b', 'postgres', 'basico.puml')
  qwen_measuring('qwen2.5:7b', 'mysql', 'basico.puml')

  qwen_tiny_measuring('qwen2.5-coder:0.5b', 'sqlite', 'basico.puml')
  qwen_tiny_measuring('qwen2.5-coder:0.5b', 'postgres', 'basico.puml')
  qwen_tiny_measuring('qwen2.5-coder:0.5b', 'mysql', 'basico.puml')

  deepseek_measuring('deepseek-r1:7b', 'sqlite', 'basico.puml')
  deepseek_measuring('deepseek-r1:7b', 'postgres', 'basico.puml')
  deepseek_measuring('deepseek-r1:7b', 'mysql', 'basico.puml')

  deepseek_tiny_measuring('deepseek-coder:1.3b', 'sqlite', 'basico.puml')
  deepseek_tiny_measuring('deepseek-coder:1.3b', 'postgres', 'basico.puml')
  deepseek_tiny_measuring('deepseek-coder:1.3b', 'mysql', 'basico.puml')

  gemma_measuring('gemma2:b', 'sqlite', 'basico.puml')
  gemma_measuring('gemma2:b', 'postgres', 'basico.puml')
  gemma_measuring('gemma2:b', 'mysql', 'basico.puml')

  gemma_tiny_measuring('gemma3:1b', 'sqlite', 'basico.puml')
  gemma_tiny_measuring('gemma3:1b', 'postgres', 'basico.puml')
  gemma_tiny_measuring('gemma3:1b', 'mysql', 'basico.puml')

  mistral_measuring('mistral:7b', 'sqlite', 'basico.puml')
  mistral_measuring('mistral:7b', 'postgres', 'basico.puml')
  mistral_measuring('mistral:7b', 'mysql', 'basico.puml')

  bert_measuring('bert', 'sqlite', 'basico.puml')
  bert_measuring('bert', 'postgres', 'basico.puml')
  bert_measuring('bert', 'mysql', 'basico.puml')

  # -------------------------------------------------------

  ollama_measuring('llama3.2:3b', 'sqlite', 'innova.puml')
  ollama_measuring('llama3.2:3b', 'postgres', 'innova.puml')
  ollama_measuring('llama3.2:3b', 'mysql', 'innova.puml')

  ollama_tiny_measuring('tinyllama:1.1b', 'sqlite', 'innova.puml')
  ollama_tiny_measuring('tinyllama:1.1b', 'postgres', 'innova.puml')
  ollama_tiny_measuring('tinyllama:1.1b', 'mysql', 'innova.puml')

  qwen_measuring('qwen2.5:7b', 'sqlite', 'innova.puml')
  qwen_measuring('qwen2.5:7b', 'postgres', 'innova.puml')
  qwen_measuring('qwen2.5:7b', 'mysql', 'innova.puml')

  qwen_tiny_measuring('qwen2.5-coder:0.5b', 'sqlite', 'innova.puml')
  qwen_tiny_measuring('qwen2.5-coder:0.5b', 'postgres', 'innova.puml')
  qwen_tiny_measuring('qwen2.5-coder:0.5b', 'mysql', 'innova.puml')

  deepseek_measuring('deepseek-r1:7b', 'sqlite', 'innova.puml')
  deepseek_measuring('deepseek-r1:7b', 'postgres', 'innova.puml')
  deepseek_measuring('deepseek-r1:7b', 'mysql', 'innova.puml')

  deepseek_tiny_measuring('deepseek-coder:1.3b', 'sqlite', 'innova.puml')
  deepseek_tiny_measuring('deepseek-coder:1.3b', 'postgres', 'innova.puml')
  deepseek_tiny_measuring('deepseek-coder:1.3b', 'mysql', 'innova.puml')

  gemma_measuring('gemma2:b', 'sqlite', 'innova.puml')
  gemma_measuring('gemma2:b', 'postgres', 'innova.puml')
  gemma_measuring('gemma2:b', 'mysql', 'innova.puml')

  gemma_tiny_measuring('gemma3:1b', 'sqlite', 'innova.puml')
  gemma_tiny_measuring('gemma3:1b', 'postgres', 'innova.puml')
  gemma_tiny_measuring('gemma3:1b', 'mysql', 'innova.puml')

  mistral_measuring('mistral:7b', 'sqlite', 'innova.puml')
  mistral_measuring('mistral:7b', 'postgres', 'innova.puml')
  mistral_measuring('mistral:7b', 'mysql', 'innova.puml')

  bert_measuring('bert_innova', 'sqlite', 'innova.puml')
  bert_measuring('bert_innova', 'postgres', 'innova.puml')
  bert_measuring('bert_innova', 'mysql', 'innova.puml')

  print("Todas las pruebas completadas.")

if __name__ == "__main__":
    run_all_tests()