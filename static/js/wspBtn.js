/// <reference path="../js/app_config.js" />
/// <reference path="../js/base.js" />
/// <reference path="../js/utils.js" />
/// <reference path="../js/outside_click.js" />


/**
 * Initializes the floating WhatsApp button and its expandable menu.
 * Handles the state transitions, icon swapping with a timed delay to match 
 * CSS animations, and integrates with the click-outside-to-close utility.
 * * @function wspBtnFloatingMenuEvent
 * @returns {void}
 */
function wspBtnFloatingMenuEvent() {
    const floatingButton = document.getElementById('floating-wsp-btn');
    const floatingMenu = document.getElementById('floating-wsp-menu');
    const icon = floatingButton.querySelector('i');

    // Initial state configuration for the floating button
    floatingButton.dataset.state = 'closed';

    /**
     * Toggles the UI state of the floating button and menu.
     * Swaps icons between 'wsp' and 'cross' based on current state.
     * @returns {boolean} The new state (true for open, false for closed).
     */
    function toggleButtonState() {
        const isActive = floatingButton.dataset.state === 'open';
        
        toggleState(floatingButton);
        
        // Synchronization: wait for half of the rotation (500ms total) to swap the icon
        setTimeout(() => {
            icon.className = isActive ? APP_CONFIG.getIcon('wsp') : APP_CONFIG.getIcon('cross');
            icon.classList.add('font-xxl');
        }, 250); 
        
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
}


/**
 * Sanitizes the store's cellphone number and generates the base WhatsApp URL.
 * Removes non-numeric characters and performs validation for administrative users.
 * * @function getWspUrl
 * @returns {string|null} The formatted WhatsApp URL (wa.me) or null if invalid.
 */
function getWspUrl() {
    const number = APP_CONFIG.getStoreCellphone();

    // Remove all non-numeric characters (spaces, parentheses, hyphens)
    const formatted = number.replace(/[^\d]/g, '');

    // Validation logic for Admins
    if (formatted.length < 7 && APP_CONFIG.isAdmin) {
        openAlert("Número de WhatsApp No Válido por favor configure alguno.", 'red', 2000);
        console.error("Número de teléfono no válido");
        return null;
    }
    // esta url me deja ver desde desktop, falta probar en mobile
    return `https://api.whatsapp.com/send?phone=${formatted}`;
    // return `https://wa.me/${formatted}`;
}


/**
 * Main entry point for WhatsApp-related event listeners.
 * Configures the floating menu and populates all buttons with class '.btn-wsp'
 * with context-specific pre-filled messages.
 * * @function wspBtnEvents
 * @returns {void}
 */
function wspBtnEvents() {
    // Initialize the floating menu UI
    wspBtnFloatingMenuEvent();
    
    const baseUrl = getWspUrl();
    if (!baseUrl) return;

    // Contextual messages based on the 'data-type' attribute
    const messages = {
        navbar: 'Consulta desde el sitio web',
        menu: 'Buenos días, Quería consultar sobre formas de pago con tarjeta en el local?',
        footer: 'Consulta desde el sitio web'
    };

    const refs = document.querySelectorAll('.btn-wsp');
    refs.forEach(btn => {
        const type = btn.dataset.type;
        const msg = messages[type] || 'Consulta desde el sitio web';

        // Construct final URL with URL-encoded parameters
        // const finalUrl = `${baseUrl}?text=${encodeURIComponent(msg)}`;
        const finalUrl = `${baseUrl}&text=${encodeURIComponent(msg)}`;
        btn.setAttribute('href', finalUrl);
    });
}
