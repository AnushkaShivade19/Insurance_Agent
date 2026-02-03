document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Initialize Feather Icons
    // This turns <i data-feather="user"></i> into actual SVG icons
    if (typeof feather !== 'undefined') {
        feather.replace();
    }

    // 2. Profile Dropdown Logic
    const profileBtn = document.getElementById('profileToggle');
    const dropdownMenu = document.getElementById('profileMenu');

    if (profileBtn && dropdownMenu) {
        // Toggle on click
        profileBtn.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent click from bubbling to window
            dropdownMenu.classList.toggle('active');
        });

        // Close when clicking anywhere outside
        window.addEventListener('click', function(e) {
            if (!profileBtn.contains(e.target) && !dropdownMenu.contains(e.target)) {
                dropdownMenu.classList.remove('active');
            }
        });
    }

    // 3. Auto-Dismiss Alerts (Optional UX Improvement)
    // Hides success messages automatically after 5 seconds
    const alerts = document.querySelectorAll('.alert-success');
    if (alerts.length > 0) {
        setTimeout(() => {
            alerts.forEach(alert => {
                alert.style.transition = "opacity 0.5s ease";
                alert.style.opacity = "0";
                setTimeout(() => alert.remove(), 500);
            });
        }, 5000); // 5 Seconds
    }
});