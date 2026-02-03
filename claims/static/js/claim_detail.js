document.addEventListener('DOMContentLoaded', function() {
    
    // --- FEATURE 1: COPY CLAIM ID ---
    const claimIdElement = document.getElementById('claimId');
    if (claimIdElement) {
        claimIdElement.style.cursor = 'pointer';
        claimIdElement.title = "Click to Copy ID";
        
        claimIdElement.addEventListener('click', function() {
            const text = this.innerText.replace('#', '');
            navigator.clipboard.writeText(text).then(() => {
                alert("Claim ID copied to clipboard!");
            }).catch(err => {
                console.error('Failed to copy text: ', err);
            });
        });
    }

    // --- FEATURE 2: PRINT RECEIPT ---
    // This function is attached to the print button in HTML
    window.printReceipt = function() {
        window.print();
    };

});