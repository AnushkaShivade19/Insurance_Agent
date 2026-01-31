/* =========================
   GLOBAL VARIABLES
========================= */
const chatBox = document.getElementById("chatBox");
const userInput = document.getElementById("userInput");
const micBtn = document.getElementById("mic-btn");

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const recognition = SpeechRecognition ? new SpeechRecognition() : null;
const speechSynthesis = window.speechSynthesis;

let availableVoices = [];

/* =========================
   LOAD VOICES
========================= */
function loadVoices() {
    availableVoices = speechSynthesis.getVoices();
    console.log("Loaded voices:", availableVoices.map(v => `${v.name} (${v.lang})`));
}

// Chrome loads voices async
speechSynthesis.onvoiceschanged = loadVoices;
loadVoices();

/* =========================
   LANGUAGES
========================= */
const languageData = {
    'en-IN': 'English',
    'hi-IN': 'हिंदी',
    'mr-IN': 'मराठी',
    'ta-IN': 'தமிழ்',
    'te-IN': 'తెలుగు',
    'bn-IN': 'বাংলা',
    'gu-IN': 'ગુજરાતી',
    'kn-IN': 'ಕನ್ನಡ',
    'ml-IN': 'മലയാളം',
    'pa-IN': 'ਪੰਜਾਬੀ',
    'ur-IN': 'اردو'
};

const selectWrapper = document.querySelector('.custom-select-wrapper');
const selectTrigger = document.querySelector('.custom-select-trigger');
const optionsContainer = document.querySelector('.custom-options');
const selectedLangText = document.getElementById('selected-language-text');

/* Populate dropdown */
Object.entries(languageData).forEach(([code, name]) => {
    const opt = document.createElement('div');
    opt.className = 'custom-option';
    opt.dataset.value = code;
    opt.textContent = name;
    if (code === 'en-IN') opt.classList.add('selected');
    optionsContainer.appendChild(opt);
});

const allOptions = document.querySelectorAll('.custom-option');

selectTrigger.onclick = () => selectWrapper.classList.toggle('active');

allOptions.forEach(opt => {
    opt.onclick = async () => {
        allOptions.forEach(o => o.classList.remove('selected'));
        opt.classList.add('selected');

        selectedLangText.textContent = opt.textContent;
        selectWrapper.classList.remove('active');

        setWelcomeMessage(opt.dataset.value);

        await fetch('/chat/set-language', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                // Note: You may need to add X-CSRFToken header here for Django
            },
            body: JSON.stringify({ language: opt.dataset.value.split('-')[0] })
        });
    };
});
/* =========================
   VOICE INPUT (STT) - CORRECTED
========================= */
if (recognition) {
    recognition.interimResults = false;
    recognition.continuous = false; // Stop after one sentence for chat flow

    // 1. Start Button Handler
    micBtn.onclick = () => {
        const selectedOpt = document.querySelector('.custom-option.selected');
        // Default to 'en-IN' if nothing selected
        const lang = selectedOpt ? selectedOpt.dataset.value : 'en-IN';
        
        recognition.lang = lang; // Explicitly set the language
        console.log("Listening in:", lang);
        
        try {
            recognition.start();
            micBtn.classList.add("is-listening");
        } catch (e) {
            console.error("Mic already active or blocked", e);
        }
    };

    // 2. Result Handler (THIS WAS MISSING)
    // This function runs when the browser successfully converts speech to text
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("Heard:", transcript);
        
        // Put text into input box
        userInput.value = transcript;
        
        // Reset button UI
        micBtn.classList.remove("is-listening");
        
        // Automatically send the message
        sendMessage(); 
    };

    // 3. Cleanup Handler
    // Runs if silence is detected or recognition stops
    recognition.onend = () => {
        micBtn.classList.remove("is-listening");
    };

    // 4. Error Handler
    recognition.onerror = (event) => {
        console.error("Speech recognition error:", event.error);
        micBtn.classList.remove("is-listening");
    };
} else {
    // Hide button if browser doesn't support STT
    micBtn.style.display = "none";
}

/* =========================
   CHAT UI
========================= */
function appendMessage(text, type) {
    const wrap = document.createElement("div");
    wrap.className = type;

    const row = document.createElement("div");
    row.className = "message-row";

    const content = document.createElement("div");
    content.className = "message-content";
    
    // --- FORMATTING FIX ---
    // 1. Convert **text** to <b>text</b>
    let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<b>$1</b>');
    
    // 2. Convert * text to bullet points if not already HTML
    if (!formattedText.includes('<ul>') && formattedText.includes('* ')) {
        formattedText = formattedText.replace(/\* (.*?)(<br>|$)/g, '<li>$1</li>');
        formattedText = '<ul>' + formattedText + '</ul>';
    }
    
    // 3. Convert newlines to breaks if strictly text
    formattedText = formattedText.replace(/\n/g, '<br>');

    content.innerHTML = formattedText;
    // ----------------------

    const avatar = document.createElement("div");
    avatar.className = `avatar ${type === 'bot-message' ? 'bot-avatar' : 'user-avatar'}`;
    avatar.innerHTML = `<i data-feather="${type === 'bot-message' ? 'shield' : 'user'}"></i>`;
    
    row.appendChild(avatar);
    row.appendChild(content);
    wrap.appendChild(row);
    chatBox.appendChild(wrap);
    
    feather.replace();
    chatBox.scrollTop = chatBox.scrollHeight;
}
/* =========================
   TEXT TO SPEECH
========================= */

function speak(text, lang) {
    // 1. Check if browser has a native voice for this language
    const hasNativeSupport = availableVoices.some(v => 
        v.lang === lang || v.lang.startsWith(lang.split('-')[0])
    );

    // 2. Optimization: English and Hindi usually work natively on most devices
    // For other regional languages, prefer Server-Side for better pronunciation/availability
    const preferServerSide = !['en-IN', 'hi-IN', 'en-US', 'en-GB'].includes(lang);

    if (hasNativeSupport && !preferServerSide) {
        // --- CLIENT SIDE (Native Browser) ---
        console.log(`Using Native Browser Voice for ${lang}`);
        if (!speechSynthesis) return;
        
        speechSynthesis.cancel(); // Stop previous audio
        
        const cleanText = text.replace(/<[^>]*>/g, '');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = lang;
        
        const voice = availableVoices.find(v => 
            v.lang === lang || v.lang.startsWith(lang.split('-')[0])
        );
        if (voice) utterance.voice = voice;
        
        speechSynthesis.speak(utterance);

    } else {
        // --- SERVER SIDE (Django + gTTS) ---
        console.log(`Using Server-Side Audio for ${lang}`);
        
        // Stop any native speech
        speechSynthesis.cancel();

        // Create an audio object and play the stream from Django
        const cleanText = text.replace(/<[^>]*>/g, '');
        const audio = new Audio(`/chat/speak/?text=${encodeURIComponent(cleanText)}&lang=${lang}`);
        
        audio.play().catch(e => console.error("Audio play failed:", e));
    }
}

/* =========================
   SEND MESSAGE
========================= */
async function sendMessage() {
    const msg = userInput.value.trim();
    if (!msg) return;

    appendMessage(msg, "user-message");
    userInput.value = "";
    appendMessage("...", "bot-message");

    try {
        const res = await fetch(`/chat/get-response?userMessage=${encodeURIComponent(msg)}`);
        const data = await res.json();

        chatBox.removeChild(chatBox.lastChild);
        appendMessage(data.botResponse, "bot-message");

        const lang = document.querySelector('.custom-option.selected')?.dataset.value || 'en-IN';
        speak(data.botResponse, lang);
    } catch {
        chatBox.removeChild(chatBox.lastChild);
        appendMessage("⚠️ Network issue. Please try again.", "bot-message");
    }
}

/* =========================
   WELCOME MESSAGE
========================= */
function setWelcomeMessage(lang) {
    const msgs = {
        'en-IN': "Namaste! 🙏 I'm your BimaSakhi.",
        'hi-IN': "नमस्ते! 🙏 मैं आपकी बीमा सखी हूँ।",
        'mr-IN': "नमस्कार! 🙏 मी तुमची विमा सखी आहे.",
        'ta-IN': "வணக்கம்! 🙏 நான் உங்கள் பீமா சகி.",
        'te-IN': "నమస్తే! 🙏 నేను మీ బీమా సఖి."
    };

    chatBox.innerHTML = "";
    appendMessage(msgs[lang] || msgs['en-IN'], "bot-message");
}

function handleKeyPress(e) {
    if (e.key === "Enter") sendMessage();
}

// Initial Load
window.onload = () => {
    feather.replace(); // Initialize icons
    setWelcomeMessage('en-IN');
};