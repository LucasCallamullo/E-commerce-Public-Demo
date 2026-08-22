/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../static/js/outside_click.js" />
/// <reference path="../../../../static/js/forms.js" />
/// <reference path="../../../../static/js/forms_utils.js" />
/// <reference path="../../../../static/js/errors.js" />


/**
 * Handles authentication-related user forms such as login, logout, and registration.
 *
 * This utility function:
 * - Validates the requested action type (login, register, logout).
 * - Resolves the appropriate endpoint URL based on the action.
 * - Attaches a controlled submit handler using `handleGenericFormBase`
 *   to prevent duplicate submissions and provide UI feedback.
 * - Serializes form data to JSON and sends it via `fetch` with CSRF protection.
 * - Displays user-facing alerts in Spanish based on the action result.
 * - Redirects the user after a short delay using the backend-provided URL
 *   or a safe default.
 *
 * IMPORTANT:
 * - This function is UX-oriented and does NOT replace backend validation.
 * - All security and permission checks must be enforced server-side.
 *
 * @param {HTMLFormElement} form - The form element to be handled.
 * @param {string} action - The action type associated with the form.
 *                          Allowed values: "login", "register", "logout", 'reset_password'.
 */
async function widgetUserForms(form, action) {

    // Validate action type early to prevent unexpected behavior
    if (!action || !['login', 'register', 'logout', 'reset_password'].includes(action)) {
        openAlert("Error desconocido, por favor recargue la página.", "red", 1000);
        return;
    }

    /**
     * Centralized endpoint resolution.
     * URLs should be injected from Django templates to avoid hardcoding.
     */
    const urls = {
        login: window.BASE_URLS.login,
        logout: window.BASE_URLS.logout,
        register: window.TEMPLATE_URLS.register || "/",
        reset_password: window.BASE_URLS.password_reset
    };
    const urlForm = urls[action];
    
    await handleGenericFormBase({
        form,
        submitCallback: async () => {
            try {
                const payload = getFormPayload({ form: form });
                // Send the request to the resolved endpoint
                const response = await fetch(urlForm, {
                    method: "POST",
                    headers: {
                        "X-CSRFToken": getCookie("csrftoken"),
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });

                const data = await response.json();

                // Handle validation or permission errors
                if (!response.ok) {
                    showErrorAlerts(data);
                    throw new Error("Form validation failed");
                }

                /**
                 * Action-specific success feedback.
                 * User-facing messages remain in Spanish.
                 */
                const actionHandlers = {
                    login: () => openAlert("¡Iniciaste sesión!", "green", 1000),
                    logout: () => openAlert("Cerraste sesión.", "red", 1000),
                    register: () => openAlert("¡Cuenta creada con éxito!", "green", 1000),
                    reset_password: () => openAlert(
                        "Te enviamos un mail para poder reestablecer tu contraseña!", "green", 2500)
                };

                actionHandlers[action]?.();
                if (action != 'reset_password') {
                    // Redirect using backend-provided URL or fallback
                    const redirectUrl = data.redirect_url || "/";
                    
                    setTimeout(() => {
                        window.location.href = redirectUrl;
                    }, 1000);
                }

            } catch (error) {
                console.error("User form error:", error);
            }
        },

        // UI feedback timing aligned with redirect delay
        flag_anim: true,
        time_anim: 1000
    });
}


/* Capture events of widget user forms  */
document.addEventListener('DOMContentLoaded', () => {
    const header = document.querySelector('header')

    /**
     * User Dropdown Toggle
     * 
     * Find all user buttons (e.g., login/profile buttons) and their corresponding dropdowns.
     * For each button, set up a toggle with click-outside detection to close the dropdown
     * when clicking elsewhere on the page.
     */
    const userButtons = header.querySelectorAll('.user-button');
    const dropdown = header.querySelector('.user-dropdown');
    userButtons.forEach(btn => {
        setupClickOutsideClose({
            triggerElement: btn,   // The button that toggles the dropdown
            targetElement: dropdown,    // The dropdown to show/hide
            customToggleFn: () => {
                const isExpanded = toggleState(dropdown);
                return isExpanded;
            }
        });
    })

    /**
     * Register Forms and Close Session Forms
     */
    const form = header.querySelector('.form-user-dropdown');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = e.submitter;
            const action = btn.dataset.action;    // acciones login or logout
            await widgetUserForms(form, action);
        });

        populateFormAndSnapshot({ form: form });

        // guardamos contenido del html previo en atributo privado
        form._firstContent = form.innerHTML;

        form.addEventListener('click', (e) => {
            const btn = e.target.closest('button');
            // Si no es un botón O es el botón de submit, no hacemos nada aquí
            // El evento 'submit' ya se encargará de procesar los datos
            if (!btn || btn.type === 'submit') return;

            // 1. Lógica para mostrar formulario de recuperación
            if (btn.classList.contains('btn-reset-pw')) {
                form.innerHTML = /*html*/`
                    <p class="font-md bolder">Recuperar mi clave</p>
                    <input type="email" name="email" placeholder="Email" class="mt-1 mb-2" required>
                    
                    <button type="submit" class="btn btn-main bolder font-md px-2 py-1 mb-1" 
                    data-action="reset_password"> 
                        Recuperar
                    </button>
                    <button type="button" class="btn btn-alt bolder font-md px-2 py-1 btn-back-reset">
                        Volver
                    </button>
                `.trim();
            }

            // 2. Lógica para volver al login original
            else if (btn.classList.contains('btn-back-reset')) {
                form.innerHTML = form._firstContent;
            }
        });
    }
});
