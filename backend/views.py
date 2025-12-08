import json
import datetime
import os
import requests
import google.generativeai as genai
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from loja.models import ClienteFila 

# --- 1. CONFIGURAÇÃO ---
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.getenv("API_KEY")
N8N_URL = os.getenv("N8N_WEBHOOK_URL")

if API_KEY:
    genai.configure(api_key=API_KEY)

# --- CONTROLE DA LOJA ---
SIMULAR_LOJA_FECHADA = False 

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

# --- INICIALIZAÇÃO DO MODELO ---
chat_session = None
if API_KEY:
    try:
        model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=MANUAL_DA_LOJA)
        chat_session = model.start_chat(history=[])
    except:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=MANUAL_DA_LOJA)
            chat_session = model.start_chat(history=[])
        except:
            print("Erro ao conectar IA")

def index(request):
    return render(request, 'index.html')

def loja_esta_aberta():
    if SIMULAR_LOJA_FECHADA: return False
    # Fuso Horário Brasil (UTC-3)
    agora_utc = datetime.datetime.now(datetime.timezone.utc)
    fuso_brasil = datetime.timezone(datetime.timedelta(hours=-3))
    agora_br = agora_utc.astimezone(fuso_brasil)
    return 8 <= agora_br.hour < 18

# --- FUNÇÃO ATUALIZADA: Recebe o ID do Cliente ---
def enviar_para_n8n(texto_venda, cliente_id):
    if not N8N_URL:
        print("⚠️ N8N_URL não configurada.")
        return
    try:
        payload = {
            "data": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "resumo": texto_venda.replace("[VENDA]", "").strip(),
            "cliente": f"Sessão: {cliente_id[:8]}...", # Envia o ID único
            "origem": "Chatbot TechStore"
        }
        requests.post(N8N_URL, json=payload)
        print(f"✅ Venda do cliente {cliente_id[:5]} enviada para n8n!")
    except Exception as e:
        print(f"❌ Erro n8n: {e}")

@csrf_exempt
def chat_api(request):
    if request.method == 'POST':
        try:
            # 1. IDENTIFICA O USUÁRIO (SESSÃO)
            if not request.session.session_key:
                request.session.create() # Cria um ID se não existir
            session_id = request.session.session_key

            if not chat_session:
                return JsonResponse({'error': 'IA indisponível.'})

            data = json.loads(request.body)
            mensagem_usuario = data.get('message')

            if not mensagem_usuario:
                return JsonResponse({'error': 'Vazio'}, status=400)

            # 2. LOJA FECHADA?
            if not loja_esta_aberta():
                # Salva no banco com o ID para sabermos quem é quem na fila
                ClienteFila.objects.create(
                    nome_ou_mensagem=f"[ID: {session_id[:5]}] {mensagem_usuario}"
                )
                posicao = ClienteFila.objects.filter(atendido=False).count()
                return JsonResponse({'reply': f"🛑 Loja fechada. Você é o #{posicao} na fila."})

            # 3. LOJA ABERTA
            aviso_fila = ""
            if ClienteFila.objects.filter(atendido=False).exists():
                ClienteFila.objects.filter(atendido=False).update(atendido=True)
                aviso_fila = "🔔 [Fila processada!]\n\n"

            # Envia para IA
            response = chat_session.send_message(mensagem_usuario)
            resposta_ia = response.text

            # 4. VERIFICA VENDA E MANDA O ID DO CLIENTE
            if "[VENDA]" in resposta_ia:
                enviar_para_n8n(resposta_ia, session_id) # <--- Passamos o ID aqui
                resposta_limpa = resposta_ia.replace("[VENDA]", "🎉 Pedido Confirmado: ")
                return JsonResponse({'reply': aviso_fila + resposta_limpa})

            return JsonResponse({'reply': aviso_fila + resposta_ia})

        except Exception as e:
            print(f"Erro: {e}")
            return JsonResponse({'error': "Erro interno."})

    return JsonResponse({'error': 'Método inválido'}, status=400)