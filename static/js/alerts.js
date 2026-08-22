/// <reference path="../js/app_config.js" />
/// <reference path="../js/base.js" />
/// <reference path="../js/utils.js" />


// Cache the container globally to avoid repeated DOM lookups
const ALERTS_CONTAINER = document.getElementById('cont__alerts');

/**
 * Displays a custom alert message on the screen using centralized config.
 * * @param {string} message - The text message to display.
 * @param {'green'|'red'|'blue'|'yellow'} [color='green'] - Semantic color key.
 * @param {number} [timeout=1100] - Duration in ms before auto-removal.
 */
function openAlert(message, color = 'green', timeout = 1100) {
    if (!ALERTS_CONTAINER) return;

    // 1. Ensure container is active
    if (ALERTS_CONTAINER.dataset.state === 'closed') {
        toggleState(ALERTS_CONTAINER, true);
    }

    // 2. Map color and icons using our Centralized Config
    const iconClass = APP_CONFIG.getIconByColor(color);

    // 3. Create the Alert Element
    const alertBox = document.createElement('div');
    alertBox.className = 'alerts__alert show';
    alertBox.style.backgroundColor = APP_CONFIG.getColor(color);

    // solo por debug
    const extra = (APP_CONFIG.DEBUG) ? 
        'text-pre-wrap text-line-sm justify-self-start align-self-start grid-coll-all' : 
        'd-flex justify-self-center align-self-center';

    alertBox.innerHTML = /*html*/`
        <div class="d-grid cont-grid-2-min-end text-white">
            <span class="font-md fw-normal-plus ${extra}">
                ${message}
            </span>
            <button class="btn text-white justify-self-end align-self-end scale-on-touch" aria-label="Close alert">
                <i class="${iconClass} font-xl"></i>
            </button>
        </div>
    `;

    // 4. Cleanup Logic (Encapsulated)
    const removeAlert = () => {
        alertBox.classList.remove('show');
        // Wait for a small fade-out transition if you have one in CSS
        alertBox.remove();
        
        if (ALERTS_CONTAINER.children.length === 0) {
            toggleState(ALERTS_CONTAINER, false);
        }
    };

    // 5. Event Listeners & Timers
    const autoClose = setTimeout(removeAlert, timeout);

    alertBox.querySelector('button').addEventListener('click', () => {
        clearTimeout(autoClose); // Stop the timer if closed manually
        removeAlert();
    });

    ALERTS_CONTAINER.appendChild(alertBox);
}


/**
 * Displays error messages returned from a form submission.
 *
 * This function iterates over an error object (commonly returned by a backend API
 * such as Django REST Framework) and displays each error message as a red alert.
 * It is designed to be defensive and supports multiple possible error formats.
 *
 * Supported error formats:
 * - { field: ["error1", "error2"] }
 * - { field: "error message" }
 * - { field: { subfield: ["error"] } }
 * - { non_field_errors: ["error"] }
 *
 * Example:
 *     showErrorAlerts(data)
 * 
 * @param {Object} errors - An object containing validation or API errors.
 * @param {number} [delay=2400] - Time in milliseconds before each alert disappears.
 */
function showErrorAlerts(errors, color = 'red', delay = 2000) {
    // 1. Debug Logger: Capture the raw error object for development
    if (APP_CONFIG.DEBUG) {
        console.error(`[DEBUG] Form Validation Errors:`, {
            timestamp: new Date().toISOString(),
            data: errors
        });
    }
    
    // Defensive check: ensure errors is a valid object
    if (!errors || typeof errors !== 'object') {
        openAlert("Unexpected error occurred.", "red", delay);
        return;
    }

    // Iterate over each error entry (field name + error value)
    Object.entries(errors).forEach(([field, value]) => {

        // Case 1: Array of messages (Standard DRF validation error)
        // { "email": ["Invalid format", "Domain not allowed"] }
        if (Array.isArray(value)) {
            value.forEach(msg => {
                openAlert(msg, color, delay);
            });
        }

        // Case 2: The error value is a single string message
        // Example: { detail: "Authentication failed" }
        else if (typeof value === 'string') {
            openAlert(value, color, delay);
        }

        // Case 3: The error value is a nested object
        // Example: { email: { detail: ["Already registered"] } }
        else if (typeof value === 'object') {
            Object.values(value)
                .flat()
                .forEach(msg => {
                    openAlert(msg, color, delay);
                });
        }
    });
}

