/* =========================
   ELEMENTS
========================= */
const chat = document.getElementById("chat");
const inputEl = document.getElementById("input");
const popup = document.getElementById("popup");

let history = [];

/* =========================
   TOGGLE CHAT
========================= */
function toggleChat() {
    if (!popup) return;

    popup.style.display =
        popup.style.display === "flex" ? "none" : "flex";
}

/* =========================
   ADD MESSAGE TO UI
========================= */
function addMessage(text, sender) {
    if (!chat) return;

    const msg = document.createElement("div");
    msg.className = "msg " + sender;

    msg.innerHTML = `<div class="bubble">${text}</div>`;

    chat.appendChild(msg);
    chat.scrollTop = chat.scrollHeight;
}

/* =========================
   SEND MESSAGE (API)
========================= */
async function sendMessage() {
    const text = inputEl.value.trim();
    if (!text) return;

    addMessage(text, "user");
    inputEl.value = "";

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: text,
                history: history
            })
        });

        const data = await res.json();
        const reply = data.reply || "⚠️ No response";

        addMessage(reply, "bot");
        speak(reply);

        history.push({ role: "user", content: text });
        history.push({ role: "assistant", content: reply });

    } catch (err) {
        console.error(err);
        addMessage("⚠️ Server not running", "bot");
    }
}

/* =========================
   ENTER KEY SUPPORT
========================= */
if (inputEl) {
    inputEl.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            sendMessage();
        }
    });
}

/* =========================
   QUICK TIPS
========================= */
function sendTip(text) {
    inputEl.value = text;
    sendMessage();
}

/* =========================
   VOICE INPUT
========================= */
let recognition;

if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
    const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;

    recognition = new SpeechRecognition();
    recognition.lang = "en-US";

    recognition.onresult = function (e) {
        const text = e.results[0][0].transcript;
        inputEl.value = text;
        sendMessage();
    };

    recognition.onerror = function (e) {
        let message = "🎤 Voice error";
        if (e && e.error) {
            if (e.error === "not-allowed") {
                message = "🎤 Microphone permission denied. Please allow microphone access in your browser settings.";
            } else if (e.error === "no-speech") {
                message = "🎤 No speech detected. Please speak clearly into your microphone.";
            } else if (e.error === "network") {
                message = "🎤 Network error. Speech recognition requires an active internet connection.";
            } else if (e.error === "audio-capture") {
                message = "🎤 No microphone detected. Please check your recording device.";
            } else {
                message = `🎤 Voice error: ${e.error}`;
            }
        }
        addMessage(message, "bot");
    };
}

function startVoice() {
    if (recognition) {
        recognition.start();
    } else {
        alert("Voice not supported in this browser");
    }
}

/* =========================
   TEXT TO SPEECH
========================= */
function speak(text) {
    if (!("speechSynthesis" in window)) return;

    window.speechSynthesis.cancel();

    // Clean markdown characters from the text before sending to speech engine
    const cleanText = text
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // Remove links [text](url) -> text
        .replace(/!\[([^\]]+)\]\([^)]+\)/g, "$1") // Remove images ![alt](url) -> alt
        .replace(/#+\s+/g, "") // Remove headers
        .replace(/^\s*>\s+/gm, "") // Remove blockquotes
        .replace(/^\s*[-*+]\s+/gm, "") // Remove list bullets
        .replace(/[*_`~]/g, "") // Remove bold, italic, code block, strike markers
        .replace(/\s+/g, " ") // Normalize multiple spaces
        .trim();

    const speech = new SpeechSynthesisUtterance(cleanText);
    speech.rate = 1;

    window.speechSynthesis.speak(speech);
}

/* =========================
   AUTO GREETING
========================= */
window.onload = function () {
    setTimeout(() => {
        addMessage("🎬 Hi! Ask me for movie recommendations!", "bot");
    }, 800);
};

function openModal(id) {
  document.getElementById("modal" + id).style.display = "block";
}

function closeModal(id) {
  document.getElementById("modal" + id).style.display = "none";
}





