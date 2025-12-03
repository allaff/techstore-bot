const chatMessages = document.getElementById('messages');
const userInput = document.getElementById('user-input');
const statusText = document.getElementById('status-text');

// Variável para guardar o histórico na memória
let messageHistory = [];

// Carrega o histórico assim que a página abre
document.addEventListener("DOMContentLoaded", loadChat);

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;

    // 1. Adiciona mensagem do usuário (salva no histórico)
    addMessageToScreen(message, 'user');
    saveMessageToHistory(message, 'user'); // <--- SALVA AQUI

    userInput.value = '';

    // 2. Efeito visual
    showTypingEffect();

    try {
        const response = await fetch('/api/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });

        const data = await response.json();

        removeTypingEffect();

        if (data.error) {
            // Erros não salvamos no histórico para não poluir
            addMessageToScreen("Erro: " + data.error, 'bot');
        } else {
            // Resposta do bot (salva no histórico)
            addMessageToScreen(data.reply, 'bot');
            saveMessageToHistory(data.reply, 'bot'); // <--- SALVA AQUI
        }

    } catch (error) {
        removeTypingEffect();
        console.error('Erro:', error);
        addMessageToScreen("Erro de conexão.", 'bot');
    }
}

// --- FUNÇÃO PURAMENTE VISUAL (Apenas cria o balão) ---
function addMessageToScreen(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message', sender);
    msgDiv.innerHTML = text.replace(/\n/g, '<br>');
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

// --- FUNÇÕES DE MEMÓRIA (JSON) ---

function saveMessageToHistory(text, sender) {
    // Adiciona à lista em memória
    messageHistory.push({ text: text, sender: sender });

    // Salva no Navegador
    localStorage.setItem('techstore_history_v1', JSON.stringify(messageHistory));
    console.log("Mensagem salva no cache!");
}

function loadChat() {
    // Tenta ler do navegador
    const savedData = localStorage.getItem('techstore_history_v1');

    if (savedData) {
        // Converte de volta para lista
        messageHistory = JSON.parse(savedData);

        // Recria os balões um por um
        messageHistory.forEach(msg => {
            addMessageToScreen(msg.text, msg.sender);
        });
        console.log("Histórico carregado com sucesso!");
    }
}

// --- EFEITOS VISUAIS ---

function showTypingEffect() {
    if (statusText) {
        statusText.innerText = "Digitando...";
        statusText.style.color = "#25d366";
    }

    const typingDiv = document.createElement('div');
    typingDiv.classList.add('typing-indicator');
    typingDiv.id = 'typing-bubble';
    typingDiv.innerHTML = '<span></span><span></span><span></span>';

    chatMessages.appendChild(typingDiv);
    scrollToBottom();
}

function removeTypingEffect() {
    if (statusText) {
        statusText.innerText = "Online agora";
        statusText.style.color = "";
    }

    const typingBubble = document.getElementById('typing-bubble');
    if (typingBubble) {
        typingBubble.remove();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

userInput.addEventListener("keypress", function (event) {
    if (event.key === "Enter") sendMessage();
});

/* Em static/script.js (Adiciona no final do arquivo) */

function clearHistory() {
    // 1. Confirmação simples para não apagar sem querer
    if (!confirm("Deseja apagar todo o histórico da conversa?")) return;

    // 2. Limpa o LocalStorage
    localStorage.removeItem('techstore_history_v1');

    // 3. Reseta a variável em memória
    messageHistory = [];

    // 4. Limpa a tela visualmente
    chatMessages.innerHTML = '';

    // 5. Opcional: Adiciona um aviso visual
    const aviso = document.createElement('div');
    aviso.style.textAlign = 'center';
    aviso.style.color = '#888';
    aviso.style.fontSize = '0.8rem';
    aviso.style.margin = '10px 0';
    aviso.innerText = '--- Histórico apagado ---';
    chatMessages.appendChild(aviso);
}

/* Em static/script.js - Atualize e adicione no final */

// Variável de backup temporário
let lastDeletedHistory = null;
let toastTimeout = null; // Para controlar o tempo da mensagem

function clearHistory() {
    // 1. Se não tiver nada para apagar, ignora
    if (messageHistory.length === 0) return;

    // 2. FAZ O BACKUP ANTES DE APAGAR
    lastDeletedHistory = [...messageHistory]; // Copia a lista

    // 3. Apaga tudo
    localStorage.removeItem('techstore_history_v1');
    messageHistory = [];
    chatMessages.innerHTML = '';

    // 4. Mostra a notificação com opção de desfazer
    showUndoToast();
}

function undoClear() {
    // 1. Recupera o backup
    if (lastDeletedHistory) {
        messageHistory = lastDeletedHistory;

        // 2. Salva de volta no navegador
        localStorage.setItem('techstore_history_v1', JSON.stringify(messageHistory));

        // 3. Redesenha a tela
        chatMessages.innerHTML = ''; // Limpa para não duplicar
        messageHistory.forEach(msg => {
            addMessageToScreen(msg.text, msg.sender);
        });

        // 4. Remove a notificação imediatamente
        const toast = document.getElementById('toast-notification');
        if (toast) toast.remove();

        lastDeletedHistory = null; // Limpa o backup
    }
}

// --- FUNÇÃO VISUAL DA NOTIFICAÇÃO ---
function showUndoToast() {
    // Remove notificação anterior se houver
    const oldToast = document.getElementById('toast-notification');
    if (oldToast) oldToast.remove();
    clearTimeout(toastTimeout);

    // Cria o elemento visual
    const toast = document.createElement('div');
    toast.id = 'toast-notification';
    toast.className = 'toast-notification';

    toast.innerHTML = `
        <span>Conversa apagada.</span>
        <button class="undo-btn" onclick="undoClear()">DESFAZER</button>
    `;

    document.getElementById('chat-container').appendChild(toast);

    // Some depois de 4 segundos
    toastTimeout = setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.5s';
        setTimeout(() => {
            if (toast.parentNode) toast.remove();
            lastDeletedHistory = null; // Perde a chance de desfazer
        }, 500);
    }, 4000);
}