document.addEventListener('DOMContentLoaded', () => {
    
    // 1. FILTER LOGIC
    const filterChips = document.querySelectorAll('.filter-chip');
    filterChips.forEach(chip => {
        chip.addEventListener('click', () => {
            const category = chip.getAttribute('data-category');
            const url = new URL(window.location.href);
            if (category === 'ALL') {
                url.searchParams.delete('category');
            } else {
                url.searchParams.set('category', category);
            }
            window.location.href = url.toString();
        });
    });

    // 2. AGENT MODAL LOGIC
    const modal = document.getElementById('agentModal');
    const closeBtn = document.querySelector('.close-modal');
    const agentButtons = document.querySelectorAll('.btn-agent');
    const productNameInput = document.getElementById('modalProductName');
    const productIdInput = document.getElementById('modalProductId');
    const modalForm = document.getElementById('agentRequestForm');

    // Open Modal
    agentButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const productID = btn.getAttribute('data-id');
            const productName = btn.getAttribute('data-name');
            
            // Fill Data
            productNameInput.innerText = productName;
            productIdInput.value = productID;
            
            // Dynamic Form Action URL
            modalForm.action = `/products/product/${productID}/agent/`; 
            
            modal.classList.add('active');
        });
    });

    // Close Modal
    if(closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.classList.remove('active');
        });
    }

    // Close on outside click
    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});