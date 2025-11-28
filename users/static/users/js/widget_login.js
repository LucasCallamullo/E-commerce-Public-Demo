/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../static/js/outside-click.js" />
/// <reference path="../../../../static/js/forms.js" />


/**
 * Handles the behavior for user-related forms, such as login, logout, or registration.
 * 
 * This utility:
 * - Attaches a submit handler to the given form.
 * - Prevents multiple submissions with handleGenericFormBase.
 * - Sends the form data as JSON using fetch with CSRF protection.
 * - Displays success or error alerts in Spanish.
 * - Redirects the user after a short delay based on the action type.
 *
 * @param {HTMLFormElement} form - The form element to handle.
 */
async function widgetUserForms(form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.submitter;
        const urlForm = encodeURI(btn.dataset.url);
        const action = btn.dataset.action;
        if (!urlForm || !action) return;

        await handleGenericFormBase({
            form: form,
            submitCallback: async () => {
                try {
                    // Convert the FormData to JSON
                    const formData = new FormData(form);
                    const jsonData = Object.fromEntries(formData.entries());

                    // Send the request to the form's action URL
                    const response = await fetch(urlForm, {
                        method: "POST",
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken'),
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify(jsonData),
                    });

                    const data = await response.json(); // Parse JSON response
            
                    // If the response is not ok, show validation errors
                    if (!response.ok) {
                        openAlert("Algunos campos estan incompletos", "red", 1000);
                        showErrorAlerts(data);
                        throw new Error("Form validation failed");
                    }
                    
                    // Determine the redirect URL based on the action type
                    let url = "/";
                    if (action === 'Login') {
                        openAlert("Login exitoso!" || data.message, "green", 1000);
                        url = window.BASE_URLS.profileUser;
                    } else if (action === 'Close') {
                        openAlert("Cerraste sesión." || data.message, "red", 1000);
                        // Default url = "/" → go to home
                    } else if (action === 'Register') {
                        openAlert("Cuenta creada con éxito!" || data.message, "green", 1000);
                        url = window.BASE_URLS.profileUser;
                    } else {
                        // Fallback check for unexpected actions
                        openAlert(data.error || "Uknown action.", "red", 1000);
                        throw new Error("Unknown action type");
                    }

                    // Redirect after a short delay
                    setTimeout(() => {
                        window.location.href = url;
                    }, 1000);

                } catch (error) {
                    console.error("Error:", error);
                    openAlert(`Error: ${error.message}`, "red", 2000);
                }
            },

            // Enable spinner animation and match delay to redirect delay
            flag_anim: true,
            time_anim: 1000
        });
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
    if (form) widgetUserForms(form);
});
