import google.generativeai as genai

# Cola a tua chave NOVA aqui
GOOGLE_API_KEY = "AIzaSyC7zuZFWSFDJ1X2sARdw7l-ji8_LQ9O8AI"
genai.configure(api_key=GOOGLE_API_KEY)

print("--- A CONSULTAR O GOOGLE... ---")

try:
    # Pede ao Google a lista de modelos que TU podes usar
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Modelo disponível: {m.name}")
            
except Exception as e:
    print(f"Erro ao listar: {e}")