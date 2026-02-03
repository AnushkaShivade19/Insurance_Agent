document.addEventListener('DOMContentLoaded', function() {
    
    // 1. SELECT ELEMENTS
    const micBtn = document.getElementById('micBtn');
    const statusText = document.getElementById('statusText');
    const textArea = document.getElementById('voiceInput'); // Matches forms.py ID
    const langSelect = document.getElementById('langSelect');

    // 2. CHECK BROWSER SUPPORT
    if (!('webkitSpeechRecognition' in window)) {
        alert("⚠️ Voice features require Google Chrome.");
        return;
    }

    const recognition = new webkitSpeechRecognition();
    let isListening = false;
    
    recognition.continuous = false; // Easier for mobile
    recognition.interimResults = true; // SHOWS TEXT WHILE SPEAKING!

    // 3. START/STOP LOGIC
    micBtn.addEventListener('click', () => {
        if (isListening) {
            recognition.stop();
        } else {
            recognition.lang = langSelect.value;
            recognition.start();
        }
    });

    // 4. ON START
    recognition.onstart = () => {
        isListening = true;
        document.querySelector('.voice-section').classList.add('listening');
        micBtn.classList.add('active');
        statusText.innerText = "🔴 Listening... Speak now!";
        statusText.style.color = "#dc2626";
    };

    // 5. ON END
    recognition.onend = () => {
        isListening = false;
        document.querySelector('.voice-section').classList.remove('listening');
        micBtn.classList.remove('active');
        statusText.innerText = "Tap mic to speak again";
        statusText.style.color = "#64748b";
    };

    // 6. ON RESULT (THE MAGIC)
    recognition.onresult = (event) => {
        let finalTranscript = '';
        
        // Loop through results (handles interim results too)
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
                finalTranscript += event.results[i][0].transcript;
            }
        }

        // Determine where to append
        if (finalTranscript) {
            const currentText = textArea.value;
            // Append with a space if there is already text
            textArea.value = currentText ? currentText + " " + finalTranscript : finalTranscript;
        }
    };

    // 7. ON ERROR
    recognition.onerror = (event) => {
        console.error(event.error);
        statusText.innerText = "❌ Error. Try closer to mic.";
    };
});