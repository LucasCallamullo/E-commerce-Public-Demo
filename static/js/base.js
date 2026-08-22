/// <reference path="../js/alerts.js" />
/// <reference path="../js/app_config.js" />
/// <reference path="../js/backToTopBtn.js" />
/// <reference path="../js/errors.js" />
/// <reference path="../js/forms_utils.js" />
/// <reference path="../js/forms.js" />
/// <reference path="../js/outside_click.js" />
/// <reference path="../js/overlay_modal.js" />
/// <reference path="../js/utils.js" />
/// <reference path="../js/wspBtn.js" />


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
 * Main Event Orchestrator.
 * * This listener acts as the entry point for the frontend application. 
 * It ensures that all specialized modules and event listeners are 
 * initialized only after the DOM is fully loaded and parsed.
 * * Execution order:
 * 1. WhatsApp Button Logic
 * 2. Navigation Utilities (Back to Top)
 * 3. Diagnostic Tools (DOM Analysis)
 * 4. User Interface State (Theme Manager)
 */
document.addEventListener('DOMContentLoaded', function() {

    // Initializes WhatsApp floating menu and contextual message buttons
    wspBtnEvents();

    // Initializes the 'Back to Top' scroll spy and progress indicator
    eventBackToTopBtn();

    // Executes DOM performance analysis (Runs for a limited set of iterations)
    // Diagnostic tools - Only runs if debug is explicitly enabled
    if (APP_CONFIG.debug) {
        console.warn("[System]: Debug mode is ON. Running DOM analysis...");
        analyzeHTML(1);
    }
    
    // Initializes Light/Dark mode based on local storage or system preferences
    initThemeManager();
    initFooterDescriptions();    // store-description
});


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
 * Debounce utility to limit the rate at which a function can fire.
 * Useful for performance-heavy tasks like window resizing or scrolling.
 * * @param {Function} func - The function to be executed.
 * @param {number} wait - Delay in milliseconds.
 * @returns {Function} - A debounced version of the original function.
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}


/**
 * Formats a number by adding dots as thousand separators.
 * 
 * @param {number|string} number - The number to be formatted (can be an integer, float, or string).
 * @param {bool} allowZero - This flag allow returns Zero for some case.
 * @returns {string} The formatted number as a string with dots as thousand separators.
 */
function formatNumberWithPoints(number, allowZero = false) {
    // If the value is null, undefined, or an empty string, return a blank space
    if (number === null || number === undefined || number === "") return " ";

    // Convert the string value to a number
    const price = parseFloat(number);
    
    // Check if the price is 0
    if (price === 0) 
        if (!allowZero) return 'Gratis';
        else return price;

    // If the number is an integer, format it with thousand separators using dots
    if (Number.isInteger(price)) return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");

    // If the number has decimals, format it by separating thousands with dots and decimals with a comma
    let [integerPart, decimalPart] = price.toString().split(".");
    integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    
    return decimalPart ? `${integerPart},${decimalPart}` : integerPart;
}


/**
 * Recursively escapes all string values within a given object or array.
 * This function traverses deep nested structures (objects and arrays) 
 * and applies HTML escaping to every string found.
 * * @param {any} obj - The object, array, or string to be deeply sanitized.
 * @returns {any} A new structure with all string values escaped.
 */
function deepEscape(obj) {
    // Case 1: Base case - it's a string
    if (typeof obj === 'string') return escapeHTML(obj);
    
    // Case 2: Iterative case - it's an array
    if (Array.isArray(obj)) return obj.map(deepEscape);
    
    // Case 3: Recursive case - it's an object
    if (typeof obj === 'object' && obj !== null) {

        // Si es una instancia de Date, la devolvemos tal cual
        if (obj instanceof Date) return obj;

        const escaped = {};
        for (const key in obj) {
            // Usamos hasOwnProperty para no escapar propiedades del prototipo
            if (Object.prototype.hasOwnProperty.call(obj, key)) {
                escaped[key] = deepEscape(obj[key]);
            }
            // Apply deepEscape to each property
            // escaped[key] = deepEscape(obj[key]);
        }
        return escaped;
    }
    
    // Case 4: Primitive values (numbers, booleans, null) are returned as is
    return obj;
}


/**
 * Sanitizes a string by escaping special HTML characters.
 * Converts characters like <, >, &, ", and ' into their respective 
 * HTML entities to prevent XSS (Cross-Site Scripting) attacks.
 * * @param {string} str - The raw string to be escaped.
 * @returns {string} The sanitized string with HTML entities.
 */
function escapeHTML(str) {
    if (typeof str !== 'string') return str;
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


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
