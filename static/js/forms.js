/// <reference path="../js/base.js" />
/// <reference path="../js/alerts.js" />
/// <reference path="../js/errors.js" />
/// <reference path="../js/forms_utils.js" />

/**
 * @file forms.js
 * @description Core Form Engine. 
 * Provides UI orchestration, data hydration, and change detection (Dirty Checking).
 * 
 * @function handleGenericFormBase
 * @function getFormChanges
 * @function getFormPayload
 * @function populateAndSnapshot
 * 
 */

/**
 * Handles a generic form submission with consistent UI states.
 * * Prevents multiple submissions, blocks UI interactions while the async task runs,
 * shows optional loading animations, restores UI state, and catches specific AppErrors.
 *
 * @param {Object} params - The configuration object.
 * @param {HTMLFormElement} params.form - The form element being handled.
 * @param {Function} [params.submitCallback] - Async logic to execute (e.g., fetch).
 * @param {Function} [params.closeCallback] - Logic to run after a successful submission.
 * @param {Function} [params.errorCallback] - Logic to run if an error occurs.
 * @param {number} [params.time_anim=0] - Extra delay (ms) for the loading state.
 */
async function handleGenericFormBase({
    form,
    submitCallback = () => {},
    closeCallback = () => {},
    errorCallback = () => {},
    time_anim = 0,
    isRedirect = false     // New: Skip delays if the page will change
} = {}) {
    // 1. Prevent double submissions
    if (form._isSubmitting) return;
    form._isSubmitting = true;

    const flag_anim = (time_anim > 0);
    const submitButtons = form.querySelectorAll('button[type="submit"]');

    // ---- UI Helpers ----
    const startLoading = () => {
        document.body.style.pointerEvents = 'none'; // Block global interactions

        submitButtons.forEach(btn => {
            btn.disabled = true;
            // Store original content to restore it later
            if (!btn.dataset.originalText) btn.dataset.originalText = btn.innerHTML;

            // Do not apply spinner animation if flag is false
            if (!flag_anim) return;    
            btn.innerHTML = /*html*/`
                <svg class="spinner" viewBox="0 0 66 66" xmlns="http://www.w3.org/2000/svg">
                    <circle class="path" cx="33" cy="33" r="30"></circle>
                </svg>
                <span>${btn.dataset.originalText}</span>
            `;
        });
    };

    const resetUI = () => {
        document.body.style.pointerEvents = '';
        submitButtons.forEach(btn => {
            btn.disabled = false;
            if (flag_anim) btn.innerHTML = btn.dataset.originalText;
        });
        form._isSubmitting = false;
    };

    // ---- Main Flow ----
    let successData = null; // data fetch to track execution
    let isSuccess = false;

    try {
        startLoading();
        successData = await submitCallback();    // If we reach here, it was successful
        isSuccess = true;

    } catch (err) {
        // Log error with the custom name defined in errors.js (ValidationError, BackendError, etc.)
        console.warn(`[${err.name || 'Error'}]: ${err.message}`);

        // Dispatch alerts based on the Error Type
        if (err instanceof ValidationError) {
            // Client-side or business logic error
            openAlert(err.message, err.color, err.time);
            
        } else if (err instanceof BackendError) {
            // Server-side error (handling field-specific JSON data)
            showErrorAlerts(err.data, err.color, err.time);

        } else {
            // Unexpected JavaScript errors (Syntax, Reference, etc.)
            openAlert(err.message || 'Error inesperado en el servidor', "red", 2500);
        }

        if (typeof errorCallback === 'function') errorCallback(err);
        /*/ Future-proof: focus on the problematic field
        if (err.field) {
            const el = form.querySelector(`[name="${err.field}"]`);
            el?.focus();
        } */

    } finally {
        // 1. We separate 'alert' from the rest of the data using the REST operator (...)
        const { alert, ...cleanData } = successData || {};
        
        // 2. Alert Logic (Centralizada pero opcional)
        if (alert) {
            /**
             * @example
             * 
             * const data = await api.patch(...);
             * return { ...data, alert: { msg: '¡Guardado con éxito!' } };
             */
            openAlert(alert.msg, alert.color || 'green', alert.time || 2000);
        }

        // Handle success callback (e.g., closing a modal)
        // Execute close callback after UI is restored
        if (isSuccess && typeof closeCallback === 'function') {
            closeCallback(cleanData);
        }

        // ---- Intelligent Delay Logic ----
        // If it's a redirect, we don't want to wait. If not, we wait for a smoother feel.
        const baseDelay = isRedirect ? 0 : (time_anim || 300);

        if (baseDelay > 0) {
            setTimeout(resetUI, baseDelay);
        } else {
            resetUI();
        }

        // ----- Debug Helper
        if (successData && APP_CONFIG.DEBUG) {
            console.groupCollapsed(`%c [SUCCESS]: ${form.id || 'Form'}`, 'color: #28a745; font-weight: bold;');
            
            console.log("%cPayload Structure:", "color: #5dade2; font-weight: bold;");
            console.log(JSON.stringify(cleanData, null, 4));

            // console.table(successData);
            // console.log('Response:', successData);
            console.groupEnd();
        }
    }
}


/**
 * Dynamically populates a form and creates an initial data snapshot for change tracking.
 * Hydrates the form and updates the state snapshot.
 * 
 * * This function:
 * 1. Iterates through all form elements.
 * 2. Hydrates fields with values from the 'data' object based on the 'name' attribute.
 * 3. Handles specific behaviors for checkboxes, radios, and readonly/disabled fields.
 * 4. Stores a "snapshot" in form._initialValues to enable future Dirty Checking.
 * * @param {HTMLFormElement} form - The <form> element to populate.
 * @param {Object} data - The source data object (e.g., store, network, product).
 */
function populateFormAndSnapshot({ 
    form = null, 
    data = {},
    resetForm = false,
    showDebug = true
} = {}) {
    // Get all form controls (input, textarea, select)
    if (!form && APP_CONFIG.DEBUG) logger('Falta FORM en populateFormAndSnapshot()', 'red');
    const elements = form.elements;

    // bandera especifica para modales compartidos resetear estados entre ellos
    if (resetForm) form._initialValues = {}

    // --- STRATEGY: Merge data ---
    // If we already have initial values, we merge them with the incoming data.
    // This ensures that partial 'changes' don't wipe out the rest of the snapshot.
    const combinedData = { ...(form._initialValues || {}), ...data };    // combino diccionarios
    const snapshot = {}; 

    for (let element of elements) {
        const fieldName = element.name;

        // Skip elements without a name attribute, submit buttons, or standard buttons
        if (!fieldName || element.type === 'submit' || element.type === 'button') continue;

        // --- 1. Visual-only Population (Readonly/Disabled) ---
        // We fill these fields for the user to see, but 'continue' prevents them 
        // from being added to the change-tracking snapshot.
        if ((element.disabled || element.readOnly) && element.type !== 'checkbox' && element.type !== 'radio') {
            element.value = combinedData[fieldName] ?? "";
            // Store the string value but not its necesary to getChangesForm
            snapshot[fieldName] = element.value;
            continue;
        }

        // --- 2. Data Hydration ---
        // Check if the element's 'name' exists as a key in our combinedData object
        if (combinedData.hasOwnProperty(fieldName)) {
            if (element.type === 'checkbox') {
                // Double negation (!!) forces the value to a boolean (true or false)
                element.checked = !!combinedData[fieldName];

            } else if (element.type === 'radio') {
                // Mark the radio as checked if its value matches the data source
                element.checked = (element.value === String(combinedData[fieldName]));

            } else {
                // Standard population for select, text, tel, email, and textarea
                element.value = combinedData[fieldName] ?? "";
            }
        }

        // --- 3. Snapshot Creation (Initial "Photo") ---
        if (element.type === 'radio') {
            // For radios, we only store the value of the currently selected option
            if (element.checked) {
                snapshot[fieldName] = element.value;

            } else if (!snapshot.hasOwnProperty(fieldName)) {
                snapshot[fieldName] = ""; // Default if none are selected yet
            }
        } 
        else if (element.type === 'checkbox') {
            // Store the boolean state
            snapshot[fieldName] = element.checked;
        } 
        else {
            // Store the string value
            snapshot[fieldName] = element.value;
        }
    }

    // Attach the snapshot to the form object for future comparison
    form._initialValues = snapshot;

    // Temporary debug log
    if (APP_CONFIG.DEBUG && showDebug) {
        logger(`Snapshot created for ${getLoggerFormUtils(form, form._initialValues)}`, 
            'blue', 7000);
    }
}


/**
 * Detects changes in a form by comparing current values against the initial snapshot.
 * 
 * @param {HTMLFormElement} form - The form to inspect.
 * @param {Function} beforeDiff - Validation logic before calculating changes.
 *     - (payload, initialSnapshot) => {error, field, message, color, time}
 * @param {Function} afterDiff - Validation logic based on the detected changes.
 *     - (payload, initialSnapshot) => {error, field, message, color, time}
 * 
 * * @returns {Object} - An object containing only the changed fields (delta)
 * @throws {Error} - Propagates validation errors from getCleanValueFormOrError or extraValidator.
 * 
 */
function getFormChanges({
    form = null,
    beforeDiff = null,     // Se ejecuta con los valores iniciales
    afterDiff = null,       // Se ejecuta con los cambios detectados (payload)
    emptyMessage = "No se detectaron cambios."   // Se ejecuta con los cambios detectados (payload)
} = {}) {
    // stupid check
    if (!form) {
        throw new ValidationError({
            message: 'Falta el form de getFormChanges()',
            color: 'red',     
            time: 2000           
        });
    }

    // Retrieve the initial snapshot stored during form population
    const initialSnapshot = form._initialValues || {};    // datos from populateAndSnapshot().
    const payload = {};            // payload: its changes in the form

    // --- 1. Pre-Validation (Before calculating diff) ---
    if (Object.keys(initialSnapshot).length > 0 && beforeDiff) {
        const result = beforeDiff(payload, initialSnapshot);
        // Create a standard JS Error with the custom message and throw if error
        if (result?.error) throw new ValidationError(result);
    }

    for (const el of form.elements) {
        // Skip elements without names, buttons, or non-editable fields
        if (!el.name || el.type === 'submit' || el.type === 'button') continue;
        if (el.disabled || el.readOnly) continue;

        const initial = initialSnapshot[el.name];
        
        // Pass the initial value to activate "diff mode" inside getCleanValueFormOrError.
        // It returns the sanitized value ONLY if it differs from the initial one.
        const sanitized = getCleanValueFormOrError({ element: el, initial: initial });
        
        if (sanitized != null) {
            payload[el.name] = sanitized;
            
            /* / Debugging textarea behavior 
            if (APP_CONFIG.DEBUG && el.name === 'description') {
                logger(`INITIAL Description: ${initial}`);
                logger(`FINAL Description: ${sanitized}`);
            } */
        }
    }

    // * Debugging the resulting delta payload
    if (APP_CONFIG.DEBUG) {
        logger(`[FIRST] Changes detected by getFormChanges() for ${getLoggerFormUtils(form, payload)}`, 
            'blue', 7000);
    }
    // --- Extra Validation (Business Logic) ---
    // Runs only if changes were detected and a validator is provided.
    if (Object.keys(payload).length > 0 && afterDiff) {
        const result = afterDiff(payload, initialSnapshot);
        // Create a standard JS Error with the custom message and throw if error
        if (result?.error) throw new ValidationError(result);
    }

    // * Debugging the resulting delta payload
    if (APP_CONFIG.DEBUG) {
        logger(`[SECOND] Changes detected by getFormChanges() for ${getLoggerFormUtils(form, payload)}`, 
            'green', 7000);
    }

    // throw error if is empty
    if (Object.keys(payload).length == 0) {
        // capaz en el futuro pasar mas personalización 
        throw new ValidationError({
            message: emptyMessage,
            color: 'blue',     
            time: 2500           
        });
    }

    // Returns the payload (delta) if not empty
    return payload;
}


/**
 * Validates and sanitizes a form before submission (CREATE forms).
 *
* @param {HTMLFormElement} form - The form to inspect.
 * @param {Function} beforeDiff - Hook executed before form processing. Receives the empty payload object.
 *     - (payload) => {error, message, field, color}.
 * @param {Function} afterDiff - Hook executed after gathering all values. Receives the populated payload.
 *     - (payload) => {error, message, field, color}.
 * 
 * * @returns {Object} - An object containing only the changed fields (delta)
 * @throws {Error} - Propagates validation errors from getCleanValueFormOrError or extraValidator.
 * 
 */
function getFormPayload({
    form = null,
    beforeDiff = null, // Se ejecuta con los valores iniciales
    afterDiff = null,   // Se ejecuta con los cambios detectados (payload)
    emptyMessage = "No se detectaron cambios."
} = {}) {
    // stupid check
    if (!form) {
        throw new ValidationError({
            message: 'Falta el form de validateFormOnCreate()',
            color: 'red',     
            time: 2500           
        });
    }

    // Retrieve the initial snapshot stored during form population
    const payload = {};

    // --- 1. Pre-Validation (Before calculating diff) ---
    if (beforeDiff) {
        const result = beforeDiff(payload);
        // Create a standard JS Error with the custom message and throw if error
        if (result?.error) throw new ValidationError(result);
    }

    for (const el of form.elements) {
        // Skip elements without a name, buttons, or those that are disabled/readonly
        if (!el.name || el.type === 'submit' || el.type === 'button') continue;
        if (el.disabled || el.readOnly) continue;

        // Sanitizes the value or propagates a validation error from getCleanValueFormOrError
        const sanitized = getCleanValueFormOrError({element: el});
        
        // If the value is valid and not null, add it to the final payload
        if (sanitized != null) {
            payload[el.name] = sanitized;
        }
    }

    // --- Extra Validation (Business Logic) ---
    // If the payload has data and an afterDiff is provided, run it.
    if (Object.keys(payload).length > 0 && afterDiff) {
        const result = afterDiff(payload);
        // Create a standard JS Error with the custom message and throw if error
        if (result?.error) throw new ValidationError(result);
    }
    
    // * Debug payloads
    if (APP_CONFIG.DEBUG) {
        logger(`Payload for validateFormOnCreate() from ${getLoggerFormUtils(form, payload)}`,
            'orange', 7000);
    }

    // throw error if is empty
    if (Object.keys(payload).length == 0) {
        // capaz en el futuro pasar mas personalización 
        throw new ValidationError({
            message: emptyMessage,
            color: 'blue',     
            time: 2500           
        });
    }

    // Return the payload only if it contains data
    return payload;
}


/** 
 * @example handleGenericFormBase
 * 
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleGenericFormBase({
            form: form,
            submitCallback: async () => {
                // valids payload or trhows
                const changes = getFormChanges({...});

                const response = await fetch(`/api/edit/${data.id}`);
                const data = await response.json();

                if (!response.ok) throw new BackendError({});
                // your custom logic here...
            },
    
            // Optional: callback to run after successful submission
            closeCallback: () => {
                // e.g. close modal, reset form, etc.
            },
            
            // Optional: callback to run after errors
            errorCallback: () => {
                // e.g. close modal, reset form, etc.
            },
            
            // Optional: enable spinner animation on submit button
            time_anim: 1000    // or 0 is optional if flag is true
        });
    });
 */


function getLoggerFormUtils(form, data) {
    const msg = (form.dataset.action) ? `${form.dataset.action} | ` : '';
    const msg2 = (form.dataset.id) ? `ID: ${form.dataset.id}` : '';
    return `${msg} ${msg2} <pre>${JSON.stringify(data, null, 4)}</pre>`;
    // return `${msg2} ${getJsonFormatted(data)}`;
}

function getJsonFormatted(data) {
    // const debugPayload = JSON.stringify(data, null, 4);
    // alert("Respuesta del Servidor:\n" + debugPayload);
    return Object.entries(data)
    .map(([key, value]) => `${key}: ${value}`)
    .join('\n');
}