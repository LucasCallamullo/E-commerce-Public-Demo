

/// <reference path="../js/base.js" />
/// <reference path="../js/outside-click.js" />


// Function to clean up the phone number and return the WhatsApp URL
function formatPhoneNumber(cellphone) {
    // Elimina todos los caracteres no numéricos (como espacios, paréntesis, guiones)
    const formattedNumber = cellphone.replace(/[^\d]/g, '');

    // Si el número está bien formateado (empezando con un 9, después 11 dígitos)
    if (formattedNumber.length < 6) {
        console.error("Número de teléfono no válido");
        return null;
    }

    // Return the base WhatsApp URL with the cleaned number
    return `https://wa.me/${formattedNumber}`;
}


function wspBtnEvents() {
    // Get references to the DOM elements
    const floatingButton = document.getElementById('floating-wsp-btn');
    const floatingMenu = document.getElementById('floating-wsp-menu');
    const icon = floatingButton.querySelector('i');

    // Initial state configuration for the floating button
    floatingButton.dataset.state = 'closed';

    /**
     * Handles the toggle behavior for the floating button.
     * Changes its state, swaps the icon after a delay,
     * and shows or hides the floating menu.
     */
    function toggleButtonState() {
        const isActive = floatingButton.dataset.state === 'open';
        
        // First, toggle the state
        toggleState(floatingButton);
        
        // Wait for half the rotation animation before changing the icon
        setTimeout(() => {
            icon.className = isActive ? ICONS.wsp : ICONS.cross;
            icon.classList.add('font-xxl');
        }, 250); // Changed to 250ms (half of 500ms)
        
        // Show or hide the menu based on the new state
        floatingMenu.classList.toggle('show', !isActive);
        
        return !isActive;
    }

    /**
     * Sets up the click outside behavior:
     * If the user clicks outside the target, it will close automatically.
     * Uses a custom toggle function.
     */
    setupClickOutsideClose({
        triggerElement: floatingButton,
        targetElement: floatingMenu,
        customToggleFn: toggleButtonState
    });

    // Get the WhatsApp link element
    const productLink = document.getElementById('wsp-link');

    // Extract the phone number from the data attribute
    const cellphone = productLink.getAttribute('data-wsp');

    // Format the phone number into a WhatsApp URL
    const whatsappUrl = formatPhoneNumber(cellphone);

    // Create the message dynamically with product information
    const message = `Buenos días, Quería consultar sobre formas de pago con tarjeta en el local?`;

    // If the number is valid, combine the base URL with the encoded message
    if (whatsappUrl) {
        // const finalWhatsappUrl = `https://api.whatsapp.com/send?phone=${cellphone}&text=${encodeURIComponent(message)}`;
        const finalWhatsappUrl = `${whatsappUrl}?text=${encodeURIComponent(message)}`;
        // console.log(`${finalWhatsappUrl}`)
        productLink.setAttribute('href', finalWhatsappUrl);
    }
}


    
// Wait until the DOM is fully loaded before executing the script
document.addEventListener('DOMContentLoaded', function() {
    wspBtnEvents();
});
