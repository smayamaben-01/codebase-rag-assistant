import ollama

response = ollama.chat(
    model='llama3.1:8b',
    messages=[{'role': 'user', 'content': 'Count from 1 to 10 slowly.'}],
    stream=True
)

for chunk in response:
    print(chunk['message']['content'], end='', flush=True)

print()  # final newline