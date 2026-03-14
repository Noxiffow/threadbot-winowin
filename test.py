import requests

url = "http://127.0.0.1:8000/chat"
data = {"message": "Hola, ¿cuánto cuesta unos vaqueros?"}

response = requests.post(url, json=data)

if response.status_code == 200:
    print("Respuesta: ", response.json()["reply"])
else:
    print("Error: ", response.status_code, response.text)