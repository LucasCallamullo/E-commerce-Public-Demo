/// <reference path="../js/base.js" />
/// <reference path="../js/alerts.js" />


/*
 * EXAMPLE:
 * 
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleGenericFormBase({
            form: form,
            submitCallback: async () => {
                
                try {
                    const jsonData = sanitizeFormData(form);
                    const url = ...;
                    await formToSubmit(jsonData, url, 'PATCH');
                } catch (err) {
                    console.log('Error validando:', err);
                    // No hacés nada => no llega al servidor.
                }

                const response = await fetch(`/api/edit/${data.id}`);
                const data = await response.json();
                if (!response.ok) throw new Error(data.error || "Error while editing");
                // your custom logic here...

                // maybe use throw new Error("Form validation failed"); like returns
            },
    
            // Optional: callback to run after successful submission
            closeCallback: () => {
                // e.g. close modal, reset form, etc.
            },
            
            // Optional: enable spinner animation on submit button
            flag_anim: true,
            time_anim: 1000    // or 0 is optional if flag is true
        });
    });
 */

/**
 * Handles a generic form submission with consistent UI states (loading, success, error).
 *
 * This utility prevents multiple submissions, blocks UI interactions while the async task runs,
 * shows optional loading animations, restores UI state when done, and propagates errors.
 *
 * @param {Object} params - The configuration object.
 * @param {HTMLFormElement} params.form - The form element being handled.
 * @param {Function} [params.submitCallback] - The async logic to execute when submitting.
 * @param {Function} [params.closeCallback] - Optional callback to run after success.
 * @param {boolean} [params.flag_anim=false] - Whether to show a spinner animation on the submit button.
 */
async function handleGenericFormBase({
    form,
    submitCallback = () => {},
    closeCallback = () => {},
    flag_anim = false,
    time_anim = 0
} = {}) {
    // Use a private property to prevent double submissions
    if (form._isSubmitting) return;
    form._isSubmitting = true;

    const submitButtons = form.querySelectorAll('button[type="submit"]');

    // ---- UI Helpers ----
    const startLoading = () => {
        document.body.style.pointerEvents = 'none';

        submitButtons.forEach(btn => {
            btn.disabled = true;
            if (!btn.dataset.originalText) {
                btn.dataset.originalText = btn.innerHTML;
            }

            if (!flag_anim) return; // Do not apply spinner animation if flag is false
            btn.innerHTML = `
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
    try {
        startLoading();
        await submitCallback();

        if (closeCallback) setTimeout(closeCallback, time_anim+300);
        // if (closeCallback) closeCallback();

    } catch (error) {
        // console.error("Form Error:", error);
        // Example: openAlert("Error processing the request", "red", 2000);
        if (closeCallback) setTimeout(closeCallback, time_anim+300);

        throw error; // Propagate to allow external handling if needed

    } finally {
        if (time_anim > 0 && flag_anim) {
            setTimeout(resetUI, time_anim);
        } else {
            resetUI();
        }
    }
}

// Funciones auxiliares específicas por tipo
function sanitizeByInputType(value, input) {
    if (typeof value !== 'string') return value;
    
    const trimmed = value.trim();
    if (!trimmed) return '';

    switch (input.type) {
        case 'email':
            return trimmed.toLowerCase()
                         .replace(/[^\w\-@.+]/g, '');

        case 'url':
            return trimmed.replace(/[^\w\-.:\/?=&%#]/g, '');

        case 'tel':
            return trimmed.replace(/^(?:\+)?(\d)/, '$1')
                         .replace(/[^\d]/g, '');

        case 'text':
        case 'textarea':
        default:
            // Sanitización genérica para texto
            return trimmed.replace(/[<>"'`]/g, '')
                         .replace(/\s+/g, ' ');
    }
}

// Función para validar URLs
function isValidUrl(url) {
    if (!url) return false;
    try {
        new URL(url);
        return true;
    } catch (_) {
        return false;
    }
}

// Función para validar emails
function isValidEmail(email) {
    if (!email) return false;
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

/**
 * Sanitiza y valida datos de formulario según el tipo de campo
 * @param {HTMLFormElement} form - Elemento del formulario
 * @returns {Object} Datos procesados y validados
 * @throws {Error} Si falla alguna validación
 * 
 * Example
    try {
        const jsonData = sanitizeFormData(form);
        const url = ...;
        await formToSubmit(jsonData, url, 'PATCH');
    } catch (err) {
        console.log('Error validando:', err);
        // No hacés nada => no llega al servidor.
    }
 */
function sanitizeFormData(form) {
    const formData = new FormData(form);
    const rawData = Object.fromEntries(formData.entries());
    const processedData = {};
    const inputElements = form.elements;

    for (const [key, value] of Object.entries(rawData)) {
        const input = inputElements[key];
        if (!input) continue;

        let sanitizedValue = sanitizeByInputType(value, input);

        switch (input.type) {
            case 'email':
                if (sanitizedValue && !isValidEmail(sanitizedValue)) {
                    openAlert('Formato de email inválido.', 'red', 1500);
                    throw new Error('Formato de email inválido.');
                }
                break;

            case 'url':
                if (sanitizedValue) {
                    if (!isValidUrl(sanitizedValue)) {
                        openAlert('URL inválida.', 'red', 1500);
                        throw new Error('URL inválida.');
                    }
                    sanitizedValue = sanitizedValue.startsWith('http') ? sanitizedValue : `https://${sanitizedValue}`;
                }
                break;

            case 'tel':
                if (sanitizedValue) {
                    sanitizedValue = sanitizedValue.replace(/^(?:\+)?(\d)/, '$1').replace(/[^\d]/g, '');
                    if (sanitizedValue.length < 6 || sanitizedValue.length > 20) {
                        openAlert('Teléfono debe tener 6-20 dígitos.', 'red', 1500);
                        throw new Error('Teléfono debe tener 6-20 dígitos.');
                    }
                }
                break;

            case 'price':
                if (sanitizedValue) {
                    sanitizedValue = sanitizedValue.replace(/[^\d.]/g, '');
                    if (!/^\d+(\.\d+)?$/.test(sanitizedValue)) {
                        openAlert('El precio debe ser numérico.', 'red', 1500);
                        throw new Error('El precio debe ser numérico.');
                    }
                } else {
                    openAlert('El precio es requerido.', 'red', 1500);
                    throw new Error('El precio es requerido.');
                }
                break;
        }

        processedData[key] = sanitizedValue;
    }

    // Recorre TODOS los <select> del form:
    form.querySelectorAll('select').forEach(select => {
        processedData[select.name] = select.value;
    });

    /* select multiple case maybe in the future 
    form.querySelectorAll('select').forEach(select => {
        if (select.multiple) {
            processedData[select.name] = Array.from(select.selectedOptions).map(opt => opt.value);
        } else {
            processedData[select.name] = select.value;
        }
    }); */

    // checkboxs
    form.querySelectorAll('input[type="checkbox"]').forEach(cb => {
        processedData[cb.name] = cb.checked;
    });

    return processedData;
}

