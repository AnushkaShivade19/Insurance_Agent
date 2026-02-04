/* static/chatbot/js/chat.js */
console.log("🚀 BimaSakhi v12.0 (Full Features: Voice, Lang, Offline)");

// ========================================================
// 1. CONFIGURATION & DATA
// ========================================================
let currentAudio = null;
let currentLang = 'en-IN'; // Default Language
let recognition = null;

// MULTI-LANGUAGE GREETINGS
const GREETINGS = {
    'en-IN': "Namaste! I am BimaSakhi. How can I help you today?",
    'hi-IN': "नमस्ते! मैं बीमासखी हूँ। आज मैं आपकी कैसे मदद कर सकती हूँ?",
    'mr-IN': "नमस्ते! मी बीमासखी आहे. आज मी तुम्हाला कशी मदत करू शकते?",
    'gu-IN': "નમસ્તે! હું વિમાસખી છું. આજે હું તમારી કેવી મદદ કરી શકું?",
    'bn-IN': "নমস্কার! আমি বিমাসখি। আজ আমি আপনাকে কীভাবে সাহায্য করতে পারি?",
    'ta-IN': "வணக்கம்! நான் பீமாசகி. இன்று நான் உங்களுக்கு எப்படி உதவ முடியும்?"
};

// OFFLINE KNOWLEDGE BASE
const OFFLINE_KNOWLEDGE = [
    {
        keywords: ["hi", "hello", "namaste", "hey", "start"],
        answer: "Namaste! 🙏 I am currently in <b>Offline Mode</b>. I can still help you find agents, view policies, or guide you on claims."
    },
    {
        keywords: ["claim", "accident", "file", "report"],
        answer: "<b>Offline Claim Guide:</b><br>1. Go to <a href='/file-claim/'>File Claim</a>.<br>2. Upload photos (they will sync when internet returns).<br>3. Or call our helpline: <b>1800-123-BIMA</b>."
    },
    {
        keywords: ["policy", "status", "active", "check", "my plan"],
        answer: "You can view your active policies in the <a href='/dashboard/'>Dashboard</a>. We have saved a copy for you to view offline!"
    },
    {
        keywords: ["agent", "contact", "call", "help", "number"],
        answer: "Our helpline works without internet! Call us directly: <a href='tel:18001232462'>1800-123-BIMA</a>."
    }
];

function getLocalResponse(text) {
    if (!text) return "";
    text = text.toLowerCase();
    for (let item of OFFLINE_KNOWLEDGE) {
        for (let key of item.keywords) {
            if (text.includes(key)) return item.answer;
        }
    }
    return "I am in <b>Offline Mode</b> 📶. I can't reach the server, but I can help with 'Claims', 'Agents', or 'My Policies'.";
}

// ========================================================
// 2. MAIN SEND FUNCTION
// ========================================================
async function sendMessage() {
    const userInput = document.getElementById("userInput");
    const msg = userInput.value.trim();
    if (!msg) return;

    // 1. UI Updates
    stopAudio(); // Stop any current speech
    appendMessage(msg, "user-message");
    userInput.value = "";
    
    const loadingId = "loading-" + Date.now();
    showLoading(loadingId);

    // 2. CHECK NETWORK
    if (!navigator.onLine) {
        console.log("⚠️ Offline detected.");
        setTimeout(() => {
            const reply = getLocalResponse(msg);
            removeLoading(loadingId);
            appendMessage(reply, "bot-message");
        }, 500);
        return;
    }

    // 3. ONLINE FETCH
    try {
        const config = document.getElementById('chat-config');
        const API_URL = config ? config.dataset.apiUrl : '/chatbot/get-response/';

        // Fetch from server
        const response = await fetch(`${API_URL}?userMessage=${encodeURIComponent(msg)}`);
        const data = await response.json();
        
        removeLoading(loadingId);
        
        if (data.botResponse) {
            appendMessage(data.botResponse, "bot-message");
            playAudio(data.botResponse); // Speak the answer
        } else {
            const reply = getLocalResponse(msg);
            appendMessage(reply, "bot-message");
        }
    } catch (error) {
        console.error("Server Error:", error);
        removeLoading(loadingId);
        const reply = getLocalResponse(msg);
        appendMessage(reply, "bot-message");
    }
}

// ========================================================
// 3. AUDIO & VOICE FUNCTIONS
// ========================================================
function playAudio(text) {
    // Don't try to speak HTML tags or short text
    let cleanText = text.replace(/<[^>]*>/g, '').replace(/[*#_]/g, '');
    if (cleanText.length < 2) return;

    const config = document.getElementById('chat-config');
    const SPEAK_URL = config ? config.dataset.speakUrl : '/chatbot/speak/';
    const langShort = currentLang.split('-')[0]; // 'en', 'hi', etc.

    const audioUrl = `${SPEAK_URL}?text=${encodeURIComponent(cleanText)}&lang=${langShort}`;
    
    currentAudio = new Audio(audioUrl);
    const avatar = document.getElementById("sakhiAvatar");

    currentAudio.onplay = () => { if(avatar) avatar.classList.add("is-speaking"); };
    currentAudio.onended = () => { if(avatar) avatar.classList.remove("is-speaking"); };
    currentAudio.onpause = () => { if(avatar) avatar.classList.remove("is-speaking"); };
    
    currentAudio.play().catch(e => console.log("Audio autoplay blocked by browser"));
}

function stopAudio() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
        const avatar = document.getElementById("sakhiAvatar");
        if(avatar) avatar.classList.remove("is-speaking");
    }
}

function setupVoiceInput() {
    const micBtn = document.getElementById("mic-btn");
    const userInput = document.getElementById("userInput");

    if (micBtn && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = currentLang;

        micBtn.addEventListener("click", () => {
            if (micBtn.classList.contains("is-listening")) {
                recognition.stop();
            } else {
                stopAudio(); // Stop bot speaking
                recognition.lang = currentLang; // Update lang before starting
                recognition.start();
                micBtn.classList.add("is-listening");
                userInput.placeholder = "Listening...";
            }
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            micBtn.classList.remove("is-listening");
            sendMessage(); // Auto-send
        };

        recognition.onend = () => {
            micBtn.classList.remove("is-listening");
            userInput.placeholder = "Ask BimaSakhi...";
        };
    } else if (micBtn) {
        micBtn.style.display = 'none'; // Hide if not supported
    }
}

// ========================================================
// 4. UI HELPER FUNCTIONS
// ========================================================
function appendMessage(html, type) {
    const chatBox = document.getElementById("chatBox");
    if (!chatBox) return;
    
    const div = document.createElement("div");
    div.className = `message-row ${type === 'bot-message' ? 'bot-row' : 'user-row'}`;
    
    const avatar = type === 'bot-message' 
        ? `<div class="avatar bot-avatar"><i data-feather="shield"></i></div>`
        : `<div class="avatar user-avatar"><i data-feather="user"></i></div>`;

    div.innerHTML = avatar + `<div class="message-content">${html}</div>`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    
    if (typeof feather !== 'undefined') feather.replace();
}

function showLoading(id) {
    const chatBox = document.getElementById("chatBox");
    const div = document.createElement("div");
    div.id = id;
    div.className = "message-row bot-row";
    div.innerHTML = `<div class="avatar bot-avatar"><i data-feather="loader" class="spin"></i></div><div class="message-content">Thinking...</div>`;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    if (typeof feather !== 'undefined') feather.replace();
}

function removeLoading(id) {
    const loader = document.getElementById(id);
    if (loader) loader.remove();
}

// ========================================================
// 5. INITIALIZATION
// ========================================================
document.addEventListener("DOMContentLoaded", function() {
    const userInput = document.getElementById("userInput");
    const sendBtn = document.querySelector(".send-button");
    const chatBox = document.getElementById("chatBox");

    // SETUP VOICE
    setupVoiceInput();

    // ENTER KEY LISTENER
    if (userInput) {
        userInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault();
                sendMessage();
            }
        });
    }

    // SEND BUTTON
    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }

    // LANGUAGE DROPDOWN LOGIC
    document.querySelectorAll('.custom-option').forEach(opt => {
        opt.addEventListener('click', function() {
            currentLang = this.dataset.value;
            // Update text on screen
            document.getElementById('selected-language-text').textContent = this.textContent;
            // Send to backend
            const config = document.getElementById('chat-config');
            if(config) {
                 fetch(config.dataset.setLangUrl, {
                    method: 'POST',
                    body: JSON.stringify({ language: currentLang.split('-')[0] })
                 });
            }
        });
    });

    // INITIAL GREETING (Based on Language)
    if (chatBox && chatBox.children.length === 0) {
        setTimeout(() => {
            const greeting = GREETINGS[currentLang] || GREETINGS['en-IN'];
            appendMessage(greeting, "bot-message");
            // Optional: Speak greeting if online
            if(navigator.onLine) playAudio(greeting); 
        }, 800);
    }

    if (typeof feather !== 'undefined') feather.replace();
});