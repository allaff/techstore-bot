import json
import datetime
import os
import requests
import google.generativeai as genai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

# --- 1. CONFIGURAÇÃO DE AMBIENTE ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv não instalado.")

API_KEY = os.getenv("API_KEY")
N8N_URL = os.getenv("N8N_WEBHOOK_URL")

# --- 2. CONFIGURAÇÃO DA IA ---
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    print("❌ ERRO: API_KEY não encontrada no .env")

# --- 3. DADOS DA LOJA ---
SIMULAR_LOJA_FECHADA = False 
FILA_DE_ESPERA = []

MANUAL_DA_LOJA = """
VOCÊ É: O assistente virtual oficial da 'TechStore'.
OBJETIVO: Vender produtos.

CATÁLOGO:
- Notebook Gamer Dell: R$ 5.200,00
- Notebook Básico Lenovo: R$ 2.100,00
- Mouse Sem Fio Logitech: R$ 80,00
- Teclado Mecânico RGB: R$ 250,00
- Monitor 24" Samsung: R$ 800,00
- Cabo HDMI 2m: R$ 25,00 (ESGOTADO)

🛑 REGRA DE OURO (AUTOMAÇÃO):
Sempre que o cliente confirmar explicitamente que vai comprar (ex: "quero", "fechado"), 
você DEVE começar sua resposta com a tag [VENDA] seguida do resumo.
Exemplo: "[VENDA] 1x Notebook Dell - R$ 5.200"
"""

# --- 4. INICIALIZAÇÃO DO MODELO ---
chat_session = None
if API_KEY:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=MANUAL_DA_LOJA)
        chat_session = model.start_chat(history=[])
        print("✅ Conectado ao Gemini 2.5")
    except:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=MANUAL_DA_LOJA)
            chat_session = model.start_chat(history=[])
            print("✅ Conectado ao Gemini 1.5 (Fallback)")
        except:
            print("❌ Falha na conexão com a IA")

def index(request):
    return render(request, 'index.html')

def loja_esta_aberta():
    if SIMULAR_LOJA_FECHADA: return False
    hora = datetime.datetime.now().hour
    return 8 <= hora < 18

def enviar_para_n8n(texto_venda):
    if not N8N_URL:
        print("⚠️ N8N_URL não configurada.")
        return
    try:
        payload = {
            "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resumo": texto_venda.replace("[VENDA]", "").strip(),
            "origem": "Chatbot TechStore"
        }
        requests.post(N8N_URL, json=payload)
        print("✅ Enviado para n8n!")
    except Exception as e:
        print(f"❌ Erro n8n: {e}")

@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            # Verifica IA
            if not chat_session:
                return JsonResponse({'error': 'IA indisponível.'})

            data = json.loads(request.body)
            mensagem_usuario = data.get('message')

            if not mensagem_usuario:
                return JsonResponse({'error': 'Vazio'}, status=400)

            # 1. Loja Fechada
            if not loja_esta_aberta():
                posicao = len(FILA_DE_ESPERA) + 1
                FILA_DE_ESPERA.append(mensagem_usuario)
                return JsonResponse({'reply': f"🛑 Loja fechada. Você é o #{posicao} na fila."})

            # 2. Loja Aberta
            aviso_fila = ""
            if len(FILA_DE_ESPERA) > 0:
                FILA_DE_ESPERA.clear()
                aviso_fila = "🔔 [Fila processada!]\n\n"

            # Envia para IA
            response = chat_session.send_message(mensagem_usuario)
            resposta_ia = response.text

            # 3. Verifica Venda (N8N)
            if "[VENDA]" in resposta_ia:
                enviar_para_n8n(resposta_ia)
                resposta_limpa = resposta_ia.replace("[VENDA]", "🎉 Pedido Confirmado: ")
                return JsonResponse({'reply': aviso_fila + resposta_limpa})

            return JsonResponse({'reply': aviso_fila + resposta_ia})

        except Exception as e:
            print(f"Erro: {e}")
            return JsonResponse({'error': "Erro interno."})

    return JsonResponse({'error': 'Método inválido'}, status=400)