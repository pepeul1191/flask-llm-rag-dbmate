import ollama

def content():
  # Obtener la respuesta completa (sin streaming)
  response = ollama.chat(
    model="llama3.2",
    messages=[
      {
        "role": "user", 
        "content": "que es el futbol?"
      },
    ]
  )  # ✅ Sin stream=True y sin coma al final
  
  # Imprimir todo el contenido de golpe
  print(response["message"]["content"])

def chunks():
  res = ollama.chat(
    model="llama3.2",
    messages=[
      {
        "role": "user", 
        "content": "que es el futbol?"
      },
    ],
    stream=True
  )

  for chunk in res:
    print(chunk["message"]["content"], end="", flush=True)

def generate():
    # Mostrar información del modelo
    print("=== INFORMACIÓN DEL MODELO ===")
    ollama.show("llama3.2")
    
    print("\n=== RESPUESTA GENERADA ===")
    # Generar respuesta
    res = ollama.generate(
        model="llama3.2",
        prompt="que es el fubol?"
    )
    
    print(res["response"])

generate()