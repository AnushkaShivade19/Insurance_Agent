document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 BimaSakhi v9.0 (Voice & Enter Key Fix)");

    // 1. CONFIG & ELEMENTS
    const configDiv = document.getElementById('chat-config');
    const API_URL = configDiv.dataset.apiUrl;
    const SPEAK_URL = configDiv.dataset.speakUrl;
    const SET_LANG_URL = configDiv.dataset.setLangUrl;
    const CSRF_TOKEN = configDiv.dataset.csrf;
    const CONTEXT = configDiv.dataset.context;

    const chatBox = document.getElementById("chatBox");
    const userInput = document.getElementById("userInput");
    const micBtn = document.getElementById("mic-btn");
    const sendBtn = document.querySelector(".send-button"); // Select by class if ID missing
    const sakhiAvatar = document.getElementById("sakhiAvatar"); 
    
    // Dropdown Elements
    const selectWrapper = document.querySelector('.custom-select-wrapper');
    const selectTrigger = document.querySelector('.custom-select-trigger');
    const optionsContainer = document.querySelector('.custom-options');
    const selectedLangText = document.getElementById('selected-language-text');

    let currentAudio = null;
    let currentLang = 'en-IN'; 

    const languageData = {
        'en-IN': 'English', 'hi-IN': 'Hindi', 'mr-IN': 'Marathi',
        'gu-IN': 'Gujarati', 'bn-IN': 'Bengali', 'ta-IN': 'Tamil'
    };

    // ==========================================
    // 2. INPUT HANDLERS (FIXED)
    // ==========================================
    
    // Fix: Enter Key Support
    if (userInput) {
        userInput.addEventListener("keypress", function(event) {
            if (event.key === "Enter") {
                event.preventDefault(); // Prevent default behavior
                sendMessage();
            }
        });
    }

    // Fix: Send Button Click
    if (sendBtn) {
        sendBtn.addEventListener("click", sendMessage);
    }

    // Fix: Voice Input Logic
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (SpeechRecognition && micBtn) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.lang = currentLang;
        recognition.interimResults = false;

        micBtn.addEventListener("click", function() {
            if (micBtn.classList.contains("is-listening")) {
                recognition.stop();
            } else {
                // Update language before starting
                recognition.lang = currentLang; 
                try {
                    recognition.start();
                    micBtn.classList.add("is-listening");
                    userInput.placeholder = "Listening...";
                } catch (err) {
                    console.error("Mic Error:", err);
                    alert("Microphone access denied or blocked. Please check your browser settings.");
                }
            }
        });

        recognition.onstart = function() {
            console.log("Voice recognition started");
        };

        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            stopListeningUI();
            sendMessage(); // Auto-send after speaking
        };

        recognition.onerror = function(event) {
            console.error("Speech Error:", event.error);
            stopListeningUI();
        };

        recognition.onend = function() {
            stopListeningUI();
        };

        function stopListeningUI() {
            micBtn.classList.remove("is-listening");
            userInput.placeholder = "Ask BimaSakhi...";
        }
    } else {
        console.warn("Speech Recognition not supported in this browser.");
        if(micBtn) micBtn.style.display = 'none'; // Hide if not supported
    }

    // ==========================================
    // 3. DROPDOWN LOGIC
    // ==========================================
    Object.entries(languageData).forEach(([code, name]) => {
        const opt = document.createElement('div');
        opt.className = 'custom-option';
        opt.dataset.value = code;
        opt.textContent = name;
        if(code === currentLang) opt.classList.add('selected');
        
        opt.addEventListener('click', (e) => {
            e.stopPropagation();
            
            document.querySelectorAll('.custom-option').forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            selectedLangText.textContent = name;
            selectWrapper.classList.remove('active');
            
            currentLang = code;
            
            // Backend Sync
            if(SET_LANG_URL) {
                fetch(SET_LANG_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
                    body: JSON.stringify({ language: code.split('-')[0] })
                });
            }
            
            setWelcomeMessage(currentLang);
        });
        optionsContainer.appendChild(opt);
    });

    if (selectTrigger) {
        selectTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            selectWrapper.classList.toggle('active');
        });
    }

    window.addEventListener('click', () => {
        if (selectWrapper) selectWrapper.classList.remove('active');
    });

    // ==========================================
    // 4. PARSERS & AUDIO
    // ==========================================
    function parseMarkdown(text) {
        if (!text) return "";
        let html = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); 
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.replace(/^- (.*$)/gm, '<li>$1</li>'); 
        html = html.replace(/\n/g, '<br>'); 
        return html;
    }

    function playAudio(text) {
        if (currentAudio) { 
            currentAudio.pause();
            if(sakhiAvatar) sakhiAvatar.classList.remove("is-speaking");
        }

        let cleanText = text.replace(/<[^>]*>/g, '').replace(/[*#_]/g, '');
        cleanText = cleanText.replace("View & Buy Now", "").replace("Buy Policy Now", "");
        
        if (cleanText.trim().length < 2) return;

        const langShort = currentLang.split('-')[0];
        const audioUrl = `${SPEAK_URL}?text=${encodeURIComponent(cleanText)}&lang=${langShort}`;
        
        currentAudio = new Audio(audioUrl);
        
        if(sakhiAvatar) {
            currentAudio.onplay = () => sakhiAvatar.classList.add("is-speaking");
            currentAudio.onended = () => sakhiAvatar.classList.remove("is-speaking");
            currentAudio.onpause = () => sakhiAvatar.classList.remove("is-speaking");
        }
        
        currentAudio.play().catch(e => console.log("Audio autoplay blocked"));
    }

    // ==========================================
    // 5. SEND MESSAGE (MAIN LOGIC)
    // ==========================================
    async function sendMessage() {
        const msg = userInput.value.trim();
        if (!msg) return;

        if (currentAudio) {
            currentAudio.pause();
            if(sakhiAvatar) sakhiAvatar.classList.remove("is-speaking");
        }
        
        appendMessage(msg, "user-message");
        userInput.value = "";
        
        const loadingId = "loading-" + Date.now();
        showLoading(loadingId);

        try {
            const url = `${API_URL}?userMessage=${encodeURIComponent(msg)}&context=${encodeURIComponent(CONTEXT)}`;
            const response = await fetch(url, {
                method: 'GET',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN }
            });

            const data = await response.json();
            document.getElementById(loadingId).remove();
            
            if (data.botResponse) {
                const formattedResponse = parseMarkdown(data.botResponse);
                appendMessage(formattedResponse, "bot-message");
                playAudio(data.botResponse);
            } else {
                appendMessage("Received empty response.", "bot-message");
            }

        } catch (error) {
            const loader = document.getElementById(loadingId);
            if(loader) loader.remove();
            appendMessage("⚠️ Connection error.", "bot-message");
        }
    }

    // ==========================================
    // 6. UI HELPERS
    // ==========================================
    function appendMessage(html, type) {
        const rowDiv = document.createElement("div");
        const rowClass = type === 'bot-message' ? 'bot-row' : 'user-row';
        rowDiv.className = `message-row ${rowClass}`;
        
        const avatarClass = type === 'bot-message' ? 'bot-avatar' : 'user-avatar';
        const iconType = type === 'bot-message' ? 'shield' : 'user';
        
        const avatarHTML = `
            <div class="avatar ${avatarClass}">
                <i data-feather="${iconType}"></i>
            </div>`;
        
        const contentHTML = `<div class="message-content">${html}</div>`;
        
        // Combine (Flex handles order)
        rowDiv.innerHTML = avatarHTML + contentHTML;

        chatBox.appendChild(rowDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        if(typeof feather !== 'undefined') feather.replace();
    }

    function showLoading(id) {
        const rowDiv = document.createElement("div");
        rowDiv.id = id;
        rowDiv.className = "message-row bot-row";
        rowDiv.innerHTML = `
            <div class="avatar bot-avatar"><i data-feather="loader" class="spin"></i></div>
            <div class="message-content" style="color:#9ca3af; font-style:italic;">Thinking...</div>`;
        chatBox.appendChild(rowDiv);
        chatBox.scrollTop = chatBox.scrollHeight;
        feather.replace();
    }
    
    function setWelcomeMessage(lang) {
        if(chatBox.children.length > 0) return;
        let msg = CONTEXT ? `Namaste! I see you are interested in <b>${CONTEXT}</b>.` : "Namaste! I am BimaSakhi. How can I help you today?";
        appendMessage(msg, "bot-message");
    }
    
    setWelcomeMessage('en-IN');
});