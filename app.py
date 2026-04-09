from groq import Groq
from flask import Flask, request, jsonify, render_template_string
import os

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY = os.environ.get("GROQ_API_KEY", "")
CONTEXT_FILE = "context.txt"

# ── Context yükle ────────────────────────────────────────────────────────────
def load_context():
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""

# ── System prompt ─────────────────────────────────────────────────────────────
def get_system_prompt():
    context = load_context()
    return f"""Sen METU (Orta Doğu Teknik Üniversitesi) için çalışan bir asistansın.
SADECE aşağıdaki kurallara uy:
1. Yalnızca sana verilen context bilgisine ve METU'nun resmi bilgilerine dayanarak cevap ver.
2. Konu dışı sorulara kibarca "Bu konuda yardımcı olamam." de.
3. Emin olmadığın bilgileri uydurma, "Bu bilgiye sahip değilim." de.
4. Türkçe sor, Türkçe cevapla. İngilizce sor, İngilizce cevapla.

CONTEXT:
{context if context else "Henüz context girilmedi."}
"""

# ── Conversation history ──────────────────────────────────────────────────────
conversation_history = []

# ── Flask app ─────────────────────────────────────────────────────────────────
app = Flask(__name__)
client = Groq(api_key=API_KEY)

HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>METU Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; background: #f5f5f5; }
        h1 { color: #cc0000; }
        #chat-box { background: white; border: 1px solid #ddd; border-radius: 8px; height: 400px; overflow-y: auto; padding: 16px; margin-bottom: 12px; }
        .user { text-align: right; margin: 8px 0; }
        .user span { background: #cc0000; color: white; padding: 8px 12px; border-radius: 12px; display: inline-block; max-width: 80%; }
        .bot { text-align: left; margin: 8px 0; }
        .bot span { background: #e0e0e0; padding: 8px 12px; border-radius: 12px; display: inline-block; max-width: 80%; }
        #input-area { display: flex; gap: 8px; }
        #user-input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
        button { padding: 10px 20px; background: #cc0000; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 14px; }
        button:hover { background: #aa0000; }
    </style>
</head>
<body>
    <h1>🎓 METU Chatbot</h1>
    <div id="chat-box"></div>
    <div id="input-area">
        <input id="user-input" type="text" placeholder="Sorunuzu yazın..." onkeypress="if(event.key==='Enter') sendMessage()">
        <button onclick="sendMessage()">Gönder</button>
    </div>
    <script>
        async function sendMessage() {
            const input = document.getElementById('user-input');
            const msg = input.value.trim();
            if (!msg) return;
            addMessage(msg, 'user');
            input.value = '';
            const res = await fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({message: msg})
            });
            const data = await res.json();
            addMessage(data.response, 'bot');
        }
        function addMessage(text, sender) {
            const box = document.getElementById('chat-box');
            const div = document.createElement('div');
            div.className = sender;
            div.innerHTML = `<span>${text}</span>`;
            box.appendChild(div);
            box.scrollTop = box.scrollHeight;
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    global conversation_history
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"response": "Mesaj boş."})

    conversation_history.append({"role": "user", "content": user_message})

    try:
        messages = [{"role": "system", "content": get_system_prompt()}] + conversation_history
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=1024
        )
        assistant_message = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": assistant_message})
        return jsonify({"response": assistant_message})
    except Exception as e:
        conversation_history.pop()
        return jsonify({"response": f"Hata: {str(e)}"})

@app.route("/reset", methods=["POST"])
def reset():
    global conversation_history
    conversation_history = []
    return jsonify({"status": "Sohbet sıfırlandı."})

if __name__ == "__main__":
    app.run(debug=True, port=5000)