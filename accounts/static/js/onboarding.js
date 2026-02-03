/* =========================================
   RURAL-FIRST ONBOARDING LOGIC
   ========================================= */

let currentStep = 0;
let currentLang = 'en-IN';
let recognition;
let attemptCount = 0; 

document.addEventListener('DOMContentLoaded', () => {
    renderStep();
    if (typeof feather !== 'undefined') feather.replace();

    // Init Browser Speech
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true; 
        
        recognition.onresult = handleResult;
        recognition.onend = handleEnd;
    }
});

function renderStep() {
    const q = questions[currentStep];
    attemptCount = 0; 
    
    // 1. Update Image & Text
    const imgEl = document.getElementById('questionImage');
    if(imgEl) {
        imgEl.style.opacity = '0'; // Fade out
        setTimeout(() => {
            imgEl.src = q.image;
            imgEl.style.opacity = '1'; // Fade in
        }, 200);
    }
    
    document.getElementById('questionLabel').innerText = q.questions[currentLang];

    // 2. Generate Input
    const container = document.getElementById('inputContainer');
    let val = document.querySelector(`[name="${q.field}"]`).value || '';
    
    // Default to hidden unless we force typing later
    if (q.type === 'select') {
        let html = `<select id="tempInput" class="custom-input" onchange="manualValidate()">`;
        q.options.forEach(opt => html += `<option value="${opt[0]}">${opt[1]}</option>`);
        html += `</select>`;
        container.innerHTML = html;
    } else if (q.type === 'date') {
        container.innerHTML = `<input type="date" id="tempInput" class="custom-input" value="${val}" onchange="manualValidate()">`;
    } else {
        container.innerHTML = `<input type="text" id="tempInput" class="custom-input" value="${val}" placeholder="Type or Speak...">`;
    }

    // 3. Auto-Speak
    playQuestionAudio();
}

// --- CLIENT-SIDE SPEECH ---
function handleResult(event) {
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) finalTranscript += event.results[i][0].transcript;
    }
    if (finalTranscript) {
        // Gender Mapping
        if(questions[currentStep].field === 'gender') {
            const lowerT = finalTranscript.toLowerCase();
            if(lowerT.includes('male') || lowerT.includes('purush')) finalTranscript = 'M';
            else if(lowerT.includes('female') || lowerT.includes('mahila')) finalTranscript = 'F';
        }
        document.getElementById('tempInput').value = finalTranscript;
    }
}

function handleEnd() {
    document.getElementById('micBtn').classList.remove('recording');
    document.getElementById('statusText').innerText = "Verifying...";
    setTimeout(validateAnswer, 800); 
}

function validateAnswer() {
    const q = questions[currentStep];
    let val = document.getElementById('tempInput').value.trim();
    const regex = new RegExp(q.regex);

    if (regex.test(val)) {
        // SUCCESS
        document.querySelector(`[name="${q.field}"]`).value = val;
        
        if (currentStep < questions.length - 1) {
            currentStep++;
            renderStep();
        } else {
            document.getElementById('realForm').submit();
        }
    } else {
        // FAIL
        attemptCount++;
        if (attemptCount < 2) {
            const errorText = q.error_msg[currentLang];
            document.getElementById('statusText').innerText = "Try again...";
            playAudio(errorText);
        } else {
            document.getElementById('statusText').innerText = "Please type manually";
            const forceText = (currentLang === 'hi-IN') ? "कृपया टाइप करें।" : "Please type your answer.";
            playAudio(forceText);
            document.getElementById('tempInput').focus(); // Focus the input
        }
    }
}

function manualValidate() {
    setTimeout(validateAnswer, 500);
}

function toggleRecording() {
    if (!recognition) return alert("Use Chrome for voice.");
    recognition.lang = currentLang;
    try { recognition.start(); } catch(e) { recognition.stop(); }
    document.getElementById('micBtn').classList.add('recording');
    document.getElementById('statusText').innerText = "Listening...";
}

function playQuestionAudio() {
    playAudio(questions[currentStep].questions[currentLang]);
}

function playAudio(text) {
    const audio = new Audio(`/accounts/api/speak/?text=${encodeURIComponent(text)}&lang=${currentLang}`);
    audio.play().catch(e => console.log("Autoplay blocked"));
}

function setLang(lang) {
    currentLang = lang;
    document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
    
    if(lang.includes('en')) document.querySelectorAll('.lang-btn')[0].classList.add('active');
    if(lang.includes('hi')) document.querySelectorAll('.lang-btn')[1].classList.add('active');
    if(lang.includes('mr')) document.querySelectorAll('.lang-btn')[2].classList.add('active');
    
    renderStep();
}