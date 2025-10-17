import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "llama3.2",
    "prompt": "que es el futbol?"
}

response = requests.post(url, json=payload, stream=True)

if response.status_code == 200:
   
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            data = json.loads(decoded_line)
            # ✅ Usar los datos del chunk actual, no el 'result' inicial
            if "response" in data:
                print(data["response"], end="", flush=True)
            # También puedes verificar si es el final
            if data.get("done", False):
                print()  # Salto de línea al final
else:
    print("Error:", response.status_code)
    print(response.text)  # Para debug