document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Auto-dismiss Django Alert Messages (Success/Error)
    // ---------------------------------------------------
    const alerts = document.querySelectorAll('.alert'); // Assuming bootstrap-like alert classes if used, or custom
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 500);
            });
        }, 4000); // Disappear after 4 seconds
    }

    // 2. Input Field Animation (Floating Label effect optional)
    // ---------------------------------------------------
    const inputs = document.querySelectorAll('.form-control');
    inputs.forEach(input => {
        // Add a slight focus effect via JS if needed, 
        // mainly to handle "filled" state for labels if you use floating labels later.
        input.addEventListener('focus', () => {
            input.parentElement.classList.add('focused');
        });
        input.addEventListener('blur', () => {
            if (input.value === '') {
                input.parentElement.classList.remove('focused');
            }
        });
    });

    // 3. Simple Client-Side Password Match Check (Register Page)
    // ---------------------------------------------------
    const passwordInput = document.querySelector('input[name="password"]');
    const confirmInput = document.querySelector('input[name="confirm_password"]');
    const submitBtn = document.querySelector('button[type="submit"]');

    if (passwordInput && confirmInput) {
        confirmInput.addEventListener('input', function() {
            if (confirmInput.value !== passwordInput.value) {
                confirmInput.style.borderColor = '#ef4444'; // Red
                // Optional: Disable button
                // submitBtn.disabled = true; 
            } else {
                confirmInput.style.borderColor = '#22c55e'; // Green
                // submitBtn.disabled = false;
            }
        });
    }

    // 4. File Upload Preview (If profile picture is added)
    // ---------------------------------------------------
    const fileInput = document.querySelector('input[type="file"]');
    if (fileInput) {
        fileInput.addEventListener('change', function(e) {
            const fileName = e.target.files[0].name;
            // You can add a span element next to input to show filename
            // console.log("Selected file:", fileName); 
        });
    }
    
    // 5. Initialize Feather Icons (if used in dashboard)
    if (typeof feather !== 'undefined') {
        feather.replace();
    }
});