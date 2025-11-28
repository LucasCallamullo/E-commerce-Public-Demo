

// Stores event handlers for proper cleanup
const eventHandlersMap = new Map();

const ICONS = {
    // from alerts
    close: 'ri-close-circle-line',
    success: 'ri-checkbox-circle-line',
    error: 'ri-close-circle-line',
    wsp: 'ri-whatsapp-line',
    cross: 'ri-close-fill',
    heart: 'ri-heart-fill',
    heartEmpty: 'ri-heart-line'
};


/**
 * Defined in static/home/js/base.js
 * Toggles the state of an element/component between 'open' and 'closed'
 * based on its current state or a forced value, and triggers associated animations.
 * @param {HTMLElement} element - The element whose state is being toggled.
 * @param {boolean} [force] - Optional. If provided, forces the state to open (true) or closed (false).
 * @returns {boolean} - Returns a boolean indicating the new state (true if opened, false if closed).
 */
function toggleState(element, force) {
    let newState;
    
    // Si el elemento no tiene el atributo data-state, lo inicializamos como 'closed'
    if (!element.hasAttribute('data-state')) {
        element.setAttribute('data-state', 'null');
    }
    
    if (typeof force !== 'undefined') {
        // Si force está definido, forzar el estado al valor proporcionado
        newState = force;
    } else {
        // Si force no está definido, alternar el estado actual
        const isOpen = element.getAttribute('data-state') === 'open';
        newState = !isOpen;
    }
    
    // Establecer el nuevo estado en el atributo data-state
    element.setAttribute('data-state', newState ? 'open' : 'closed');
    
    return newState;
}


/**
 * Smoothly scrolls the page to the given section element and applies a temporary highlight effect.
 *
 * @param {HTMLElement} section - The DOM element to scroll into view.
 * @param {string} [colorClass='highlight-red'] - The CSS class to apply for the highlight effect.
 */
function scrollToSection(section, colorClass = 'highlight-red') {
    if (!section) return;

    section.scrollIntoView({ 
        behavior: 'smooth',
        block: 'start'
    });

    // Add highlight class and remove it after 2 seconds
    section.classList.add(colorClass);
    setTimeout(() => section.classList.remove(colorClass), 2000);
}



/**
 * Forces a full page reload by appending or updating a unique query parameter to the current URL.
 *
 * This technique helps to bypass browser cache by ensuring the URL is unique on each reload.
 *
 * Usage:
 * You can place this function at the end of your JS file or inside a <script> tag
 * after the page has loaded.
 */
function forceReload() {
    const url = new URL(window.location.href);
    url.searchParams.set('v', Date.now()); // Add unique parameter to bust cache
    window.location.href = url.toString();
};



/*
// Get the device state from the meta tag
put this <meta id="device-meta" data-state="desktop"> in html in a "head"

const deviceMeta = document.getElementById("device-meta");
const updateDeviceState = () => {
    const isMobile = window.innerWidth <= 768;
    deviceMeta.setAttribute("data-state", isMobile ? "mobile" : "desktop");
};

updateDeviceState(); // Set initial state

window.addEventListener("resize", updateDeviceState);

and included this verification in the functions in the future
document.addEventListener("DOMContentLoaded", function () {
    // Prevent unnecessary content loading on mobile, as this listener is only needed for desktop
    const deviceState = deviceMeta.getAttribute("data-state");
    if (deviceState === "mobile") return;

    // resto del codigo
}
*/