/// <reference path="../../../../../static/js/base.js" />
/// <reference path="../../../../../static/js/overlay_modal.js" />
/// <reference path="../../../../../users/static/users/js/widget_login.js" />


/**
 * Sends a PATCH request to update the authenticated user's profile.
 *
 * - Builds a minimal payload containing only changed fields.
 * - Sanitizes and validates form values via `getFormDiff`.
 * - Prevents unnecessary requests when no changes are detected.
 * - Uses a generic async form handler to manage loading state and UI feedback.
 *
 * @param {HTMLFormElement} form - User profile edit form.
 */
async function endpointEditUser(form) {
    const url = window.TEMPLATE_URLS.userPatch;

    let payload;

    try {
        // Compute the diff between current form values and the initial snapshot.
        // Only modified fields will be included in the PATCH payload.
        console.log(form._initialValues)
        payload = getFormDiff(form, form._initialValues);

        // If there are no changes, avoid sending the request.
        if (!Object.keys(payload).length) {
            openAlert('No hay cambios para guardar', 'orange');
            return;
        }
    } catch (err) {
        // Validation or sanitization error
        openAlert(err.message, 'red', 1500);
        return;
    }

    await handleGenericFormBase({
        form,

        submitCallback: async () => {
            try {
                const response = await fetch(url, {
                    method: 'PATCH',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken'),
                    },
                    body: JSON.stringify(payload),
                });

                const data = await response.json();

                if (!response.ok) {
                    // Backend validation or permission error
                    openAlert(data.detail || 'Error updating profile');
                    throw new Error(data.detail || 'Error while editing');
                }

                // Successful update
                openAlert('Perfil actualizado correctamente!');

                // Reload page to reflect updated user data
                setTimeout(() => {
                    window.location.reload();
                }, 800);

                /*
                 * Alternative approach (SPA-like):
                 * Update the snapshot without reloading the page.
                 *
                 * form._initialValues = {
                 *     ...form._initialValues,
                 *     ...payload
                 * };
                 */

            } catch (error) {
                // Network or unexpected error
                console.error('Network error:', error);
                openAlert('Error de conexión');
            }
        },

        // Enable submit button animation / loading state
        flag_anim: true,
        time_anim: 800
    });
}



/**
 * Initializes the logout form and related user profile UI controls.
 *
 * - Binds the logout form to the DRF API.
 * - Initializes the modal used to edit user profile data.
 * - Handles modal open/close behavior using a reusable toggle utility.
 */
function initLogoutForm() {
    // Form used to close the user session via DRF API
    const form = document.querySelector('.close-profile');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const btn = e.submitter;
        const action = btn.dataset.action;    // acciones login or logout
        await widgetUserForms(form, action);
    });

    // Event to open the "edit user profile" modal
    const btn = form.querySelector('.btn-edit');
    const modal = document.querySelector('.modal-edit-user');
    const overlay = document.querySelector('.overlay-edit-user');
    const btnClose = modal?.querySelector('.btn-close');

    setupToggleableElement({
        toggleButton: btn,
        closeButton: btnClose,
        element: modal,
        overlay: overlay
    });
}


/**
 * Initializes the user profile edit form.
 *
 * - Stores an initial sanitized snapshot of form values.
 * - Submits the form asynchronously using PATCH.
 * - Sends only the modified fields (diff-based update).
 */
function initEditUserForm() {
    const form = document.getElementById('form-edit-user');
    if (!form) return;

    // Store initial sanitized values for diff comparison
    form._initialValues = populateFormAndSnapshot({ form: form });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await endpointEditUser(form);
    });
}