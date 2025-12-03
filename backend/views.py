import json
import datetime
import os
import google.generativeai as genai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

# --- 1. IMPORTAÇÃO SEGURA DO DOTENV ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ AVISO: A biblioteca 'python-dotenv' não está instalada.")
    print("⚠️ Rode no terminal: pip install python-dotenv")

# --- 2. CARREGAMENTO DA CHAVE ---
API_KEY = os.getenv("API_KEY")

# Só configura se a chave existir
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("❌ ERRO: Chave API não encontrada no arquivo .env!")

# --- CONTROLE DA LOJA ---
SIMULAR_LOJA_FECHADA = False 
FILA_DE_ESPERA = []

MANUAL_DA_LOJA = """
VOCÊ É: O assistente virtual oficial da 'TechStore'.
SUA PERSONALIDADE: Simpático, direto, profissional e usa emojis ocasionalmente.
REGRAS:
1. Responda apenas sobre produtos da TechStore.
2. NUNCA invente produtos fora do catálogo.
3. Use os preços exatos da lista.
CATÁLOGO:
- Notebook Gamer Dell (i7, 16GB RAM, RTX 3050): R$ 5.200,00
- Notebook Básico Lenovo (i3, 4GB RAM): R$ 2.100,00
- Mouse Sem Fio Logitech: R$ 80,00
- Teclado Mecânico RGB: R$ 250,00
- Monitor 24" Samsung: R$ 800,00
- Cabo HDMI 2m: R$ 25,00 (ESGOTADO)
"""

# --- 3. INICIALIZAÇÃO SEGURA DO MODELO ---
chat_session = None # Começa vazio para não dar erro

if API_KEY:
    try:
        print("--- Tentando conectar ao Gemini 2.5 Flash... ---")
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=MANUAL_DA_LOJA)
        chat_session = model.start_chat(history=[])
        print("✅ Conectado ao Gemini 2.5 Flash!")
    except Exception as e:
        print(f"⚠️ Erro no 2.5 ({e}). Tentando fallback para 1.5...")
        try:
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=MANUAL_DA_LOJA)
            chat_session = model.start_chat(history=[])
            print("✅ Conectado ao Gemini 1.5 Flash (Fallback).")
        except Exception as e2:
            print(f"❌ Falha total na IA: {e2}")
            # O servidor continua rodando, mas sem IA.

def index(request):
    return render(request, 'index.html')

def loja_esta_aberta():
    if SIMULAR_LOJA_FECHADA: return False
    hora = datetime.datetime.now().hour
    return 8 <= hora < 18

@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            # Verifica se a IA carregou antes de tentar usar
            if not chat_session:
                return JsonResponse({'error': 'O sistema de IA está indisponível no momento (Erro de Chave ou Modelo).'})

            data = json.loads(request.body)
            mensagem_usuario = data.get('message')
            
            if not mensagem_usuario:
                return JsonResponse({'error': 'Mensagem vazia'}, status=400)

            # 1. LOJA FECHADA?
            if not loja_esta_aberta():
                posicao = len(FILA_DE_ESPERA) + 1
                FILA_DE_ESPERA.append(mensagem_usuario)
                
                msg = (f"🛑 A TechStore encerrou o expediente (08h às 18h).\n"
                       f"Você está na posição #{posicao} da fila de espera.")
                return JsonResponse({'reply': msg})

            # 2. LOJA ABERTA
            aviso_fila = ""
            if len(FILA_DE_ESPERA) > 0:
                qtd = len(FILA_DE_ESPERA)
                FILA_DE_ESPERA.clear()
                aviso_fila = f"🔔 [SISTEMA: {qtd} atendimentos pendentes iniciados!]\n\n"

            # Envia para a IA
            response = chat_session.send_message(mensagem_usuario)
            return JsonResponse({'reply': aviso_fila + response.text})
                
        except Exception as e:
            print(f"\nERRO TRATADO: {e}\n")
            return JsonResponse({'error': "Ocorreu um erro ao processar. Tente novamente."})
    
    return JsonResponse({'error': 'Método inválido'}, status=400)