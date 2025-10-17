import os
import ollama

model = "llama3.2"
input_file = "list.txt"
output_file = "cat_list.txt"

if not os.path.exists(input_file):
    print(f"El archivo {input_file} no existe")
    exit(1)

with open(input_file, "r") as f:
    items = f.read().strip()

prompt = f"""
You are an assitant that categorizes and sorts programming languages.

Here is a list o programming languages:

{items}

Please:

1. Categorize these items into appropieate categories as Old, POO, Functional
2. Sort the items alphabetically within each category.
3. Present the categorized list in a clear an organized manner. Use bullet points
"""

# print(prompt)

try:
    response = ollama.generate(model=model, prompt=prompt)
    generated_text = response.get("response", "")

    with open(output_file, "w") as f:
        f.write(generated_text.strip())

    print(f"Categorized PL list has been saved to '{output_file}'")
except Exception as e:
    print("An error ocurred: ", str(e))