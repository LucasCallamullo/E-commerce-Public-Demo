/// <reference path="../js/base.js" />
/// <reference path="../js/alerts.js" />
/// <reference path="../js/errors.js" />

/**
 * @file form_utils.js
 * @description Technical toolbox for data extraction, sanitization, and atomic validation.
 * These functions support the main engine in forms.js.
 */

/**
 * Extracts, sanitizes, and validates a form element's value, 
 * returning it only if it has changed from its initial state.
 * 
 * * Flow:
 * 1. Extracts the raw value based on input type (checkbox, radio, or standard).
 * 2. Sanitizes the value (e.g., trimming, price formatting).
 * 3. Validates the sanitized value against business rules (Regex, length).
 * 4. Compares against the initial value (Dirty Checking) to return either the 
 * new value or null if unchanged.
 * 
 * @param {Object} params - The parameter object.
 * @param {HTMLFormElement} params.element - The DOM element (input, textarea, etc.).
 * @param {any} [params.initial=null] - The initial value from the snapshot.
 * 
 * @returns {any|null} - The sanitized value if changed, or null if unchanged/irrelevant.
 * @throws {Error} - Throws a validation error if the sanitized value is invalid.
 */
function getCleanValueFormOrError({ element, initial = null }) {
    // --- 1. Extract raw value based on input type ---
    let rawValue;
    if (element.type === 'checkbox') {
        // For checkboxes, the value is the checked state (boolean)
        rawValue = element.checked;
    } else if (element.type === 'radio') {
        // Ignore unselected radio buttons; only process the checked one
        if (!element.checked) return null; 
        rawValue = element.value; 
    } else {
        rawValue = element.value;
    }

    // --- 2. Sanitization ---
    // Apply formatting/cleaning based on input type (e.g., price sanitization)
    const sanitized = sanitizeByInputType(rawValue, element);

    // --- 3. Type Validation (Regex, length, etc.) ---
    // Checks standard types (email, url, tel) or specific names (dni, etc.)
    validateByInputType(sanitized, element);

    // For 'create' operations (no initial value), return sanitized value immediately
    if (initial == null) return sanitized;

    // --- 4. Dirty Checking Logic ---
    // Ensure the initial value is comparable, defaulting to false or empty string
    const initialValue = initial !== undefined ? initial : (element.type === 'checkbox' ? false : '');

    // Normalize initial value for accurate comparison (especially for textareas/multiline strings)
    const normalizedInitial = (typeof initialValue === 'string') 
        ? sanitizeByInputType(initialValue, element) 
        : initialValue;

    // Compare sanitized current value against the normalized initial state
    if (sanitized !== normalizedInitial) {
        // Only return the value if a change is detected
        return sanitized;
    }

    // Return null if no changes were made to the field
    return null;
}

/**
 * Sanitizes a value based on the input element type.
 *
 * This function performs lightweight normalization for UX purposes.
 * It must NOT be treated as a security mechanism.
 *
 * @param {*} value - Raw input value.
 * @param {HTMLElement} input - Input element associated with the value.
 * @returns {*} Sanitized value.
 */
function sanitizeByInputType(value, input) {
    if (typeof value !== 'string') return value;

    const trimmed = value.trim();
    if (!trimmed) return '';

    // El navegador ya asigna .type === "textarea" a los elementos <textarea>
    switch (input.type) {
        case 'email':
            return trimmed
                .toLowerCase()
                .replace(/[^\w\-@.+]/g, '');

        case 'url':
            return trimmed.replace(/[^\w\-.:\/?=&%#]/g, '');

        case 'tel':
            return trimmed
                .replace(/^(?:\+)?(\d)/, '$1')
                .replace(/[^\d]/g, '');

        case 'textarea':
            // Para TEXTAREA: 
            // 1. Quitamos etiquetas peligrosas (limpieza básica)
            // 2. MANTENEMOS los saltos de línea (\n)
            return trimmed
                .replace(/\r\n/g, '\n')     // Normaliza saltos de línea
                .replace(/[<>"'`]/g, '');

        case 'text':
        default:
            // Generic text sanitization (UX-level only)
            return trimmed
                .replace(/[<>"'`]/g, '')
                .replace(/\s+/g, ' ');
    }
}

/**
 * Validates a sanitized value based on the input element type.
 *
 * Throws an error if validation fails.
 *
 * @param {*} value - Sanitized input value.
 * @param {HTMLElement} input - Input element associated with the value.
 * 
 * @throws {Error} If validation rules are not satisfied.
 */
function validateByInputType(value, input) {

    // Creamos una función interna para no repetir el "throw" con los mismos campos
    const throwValidationError = (message, color = "orange") => {
        // Usamos la clase que vive en errors.js
        throw new ValidationError({
            message: message,
            field: input.name,
            color: color
        });
    };

    switch (input.type) {
        case 'email':
            if (value && !isValidEmail(value)) {
                throwValidationError('Formato de email inválido.');
            }
            break;

        case 'url':
            if (value && !isValidUrl(value)) {
                throwValidationError('URL inválida.');
            }
            break;

        case 'tel':
            if (value && (value.length < 6 || value.length > 20)) {
                throwValidationError('Teléfono debe tener entre 6 y 20 dígitos.');
            }
            break;
    }

    // Validaciones por nombre (lógica de negocio específica)
    switch (input.name) {
        case 'dni':
        case 'dni_retire':
            if (value && (value.length < 6 || value.length > 20)) {
                const label = input.name === 'dni' ? 'DNI' : 'DNI de quien retira';
                throwValidationError(`${label} debe tener entre 6 y 20 dígitos.`);
            }
            break;
    }
}

/**
 * Checks whether a string is a valid URL.
 *
 * @param {string} url - URL string to validate.
 * @returns {boolean} True if valid, false otherwise.
 */
function isValidUrl(url) {
    if (!url) return false;
    try {
        new URL(url);
        return true;
    } catch (_) {
        return false;
    }
}

/**
 * Checks whether a string is a valid email address.
 *
 * @param {string} email - Email string to validate.
 * @returns {boolean} True if valid, false otherwise.
 */
function isValidEmail(email) {
    if (!email) return false;
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

