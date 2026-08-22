/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../static/js/utils.js" />
/// <reference path="../../../../users/static/users/js/widget_login.js" />


document.addEventListener('DOMContentLoaded', () => {
    // FORM HANDLER INITIALIZATION
    // ----------------------------
    /**
     * Initializes form handling for the registration form.
     * Note: The widgetUserForms function is imported from widget_register.js
     * which is preloaded earlier in base.html due to its script placement.
     */
    const form = document.getElementById('register-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = e.submitter;
            // users/static/users/js/widget_login.js
            const action = btn.dataset.action;    // acciones: register
            
            await widgetUserForms(form, action);
        });
    }

    // ACCOUNT BUTTON HANDLER
    const btn = document.querySelector('#have-account');
    const userBtns = document.querySelectorAll('.user-button');
    if (btn) {
        btn.addEventListener('click', (e) => {
            const index = IS_MOBILE ? 1 : 0;
            const userLoginBtn = userBtns[index];
            if (userLoginBtn) { 
                userLoginBtn.click();
                e.stopPropagation();
            }
        });
    }
});