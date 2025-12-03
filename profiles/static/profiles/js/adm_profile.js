/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../static/js/forms.js" />
/// <reference path="../../../../users/static/users/js/widget_login.js" />
/// <reference path="./tabs/tab_orders.js" />
/// <reference path="./tabs/tab_store.js" />
/// <reference path="./tabs/tab_roles.js" />


/**
 * Sends JSON data to the backend using Fetch with CSRF protection.
 *
 * This helper:
 *   - Sends the given `jsonData` to `url` using the specified HTTP `method`.
 *   - Automatically adds the CSRF token in the headers.
 *   - Parses the JSON response.
 *   - Shows any validation errors returned by the server.
 *   - Throws an error if the response is not OK to stop further logic.
 *   - Shows a success alert if the request succeeds.
 *
 * @param {Object} jsonData - The data to send in the request body.
 * @param {string} url - The endpoint URL to send the request to.
 * @param {string} method - The HTTP method to use (e.g., "PATCH", "POST").
 * @throws {Error} Throws if the server response is not OK.
 */
async function formProfileAdmToSubmit(jsonData, url, method) {
    const response = await fetch(url, {
        method: method,
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            "Content-Type": "application/json",
        },
        body: JSON.stringify(jsonData),
    });

    const data = await response.json();

    if (!response.ok) {
        if (data.errors) showErrorAlerts(data.errors);
        else openAlert(data.detail || "Error while editing");
        throw new Error(data.detail || "Error while editing");
    }

    openAlert('Se realizaron los cambios correctamente.' || data.detail);
}


/**
 * Binds submit events for all forms related to the Store tab.
 * 
 * This handles:
 *   - The main store form (general store data)
 *   - Multiple shipment method forms
 *   - Multiple payment method forms
 *
 * Each form uses `handleGenericFormBase` to ensure:
 *   - Double submit prevention
 *   - Spinner animation (optional)
 *   - CSRF protection via `formProfileAdmToSubmit`
 *   - JSON body submission with PATCH method
 * 
 * @param {HTMLElement} container - The container that holds all store tab forms.
 */
function storeTabEvents(container) {

    // Bind submit for the main store data form
    if (container.dataset.listened === 'true') return;
    container.dataset.listened = 'true';

    container.addEventListener('submit', async (e) => {
        const form = e.target;

        // Send Forms update Store Info, Payment Method or Shipment Method
        if (form.matches('.form-store-grid') || form.matches('.shipments-form') || form.matches('.payments-form')) {
            e.preventDefault();

            const objectId = form.dataset.index;
            let url;
            if (form.matches('.form-store-grid')) {
                url = window.TEMPLATE_URLS.storeUpdate.replace('{store_id}', objectId);
            } else if (form.matches('.shipments-form')) {
                url = window.TEMPLATE_URLS.shipmentUpdate.replace('{shipment_id}', objectId);
            } else {
                url = window.TEMPLATE_URLS.paymentUpdate.replace('{payment_id}', objectId);
            }

            await handleGenericFormBase({
                form: form,
                submitCallback: async () => {
                    try {
                        const jsonData = sanitizeFormData(form);
                        await formProfileAdmToSubmit(jsonData, url, 'PATCH');
                    } catch (err) {
                        throw new Error("Error Valid Form");
                    }
                },
                flag_anim: true,
                time_anim: 1000
            });
        }
    });
}


/**
 * Handles events related to the users tab:
 * - Submits individual role-edit forms via PATCH requests using a generic handler.
 * - Submits the main user filter/search form via GET request to update the user list.
 * - Automatically submits the filter form when the role select is changed.
 *
 * @param {HTMLElement} container - The container element holding the users tab content.
 * @param {string} tabId - The current tab identifier (used to build URLs).
 */
function usersTabEvents(container, tabId) {
    // Prevent attaching duplicate event listeners
    if (container.dataset.listened === 'true') return;
    container.dataset.listened = 'true';

    /**
     * Handle submit events for both individual user forms and the main filter form.
     */
    container.addEventListener('submit', async (e) => {
        const form = e.target;

        // If the form is an individual role-edit form
        if (form.matches('.form-user-role')) {
            e.preventDefault();

            await handleGenericFormBase({
                form: form,
                submitCallback: async () => {
                    try {
                        // Convert form data into a JSON object
                        const jsonData = sanitizeFormData(form);

                        // Build the endpoint URL using the user ID from the form's dataset
                        const url = window.TEMPLATE_URLS.userRoleUpdate.replace('{user_id}', form.dataset.index);

                        // Submit the form using a PATCH request
                        await formProfileAdmToSubmit(jsonData, url, 'PATCH');
                    } catch (err) {
                        throw new Error("Error Valid Form");
                    }
                },
                flag_anim: true,    // Enable animation after successful submission
                time_anim: 1000     // Animation duration (ms)
            });
        }

        // If the form is the main filter/search form
        if (form.matches('#form-user-table-tab')) {
            e.preventDefault();

            // Serialize form data as query string
            const formData = new FormData(form);
            const params = new URLSearchParams(formData).toString();

            await getTabContentAJAX({ container, tabId, params })
        }
    });

    /**
     * Automatically submit the main filter form when the role select changes.
     */
    container.addEventListener('change', (e) => {
        if (e.target.matches("select[name='role']")) {
            const form = e.target.closest('form');
            if (form?.matches('#form-user-table-tab')) {
                form.requestSubmit();
            }
        }
    });
}


/**
 * Initializes event listeners for the "Orders" tab content.
 * This function ensures that listeners are only attached once per tab load.
 *
 * @param {HTMLElement} container - The DOM element that contains the orders tab content.
 * @param {string} tabId - The ID of the current active tab (used for URL resolution).
 */
function ordersTabEvents(container, tabId) {
    // Avoid attaching duplicate event listeners if already initialized
    if (container.dataset.listened === 'true') return;
    container.dataset.listened = 'true';

    /**
     * Handle form submission inside the container.
     * Submits the form via AJAX and updates the container with new content.
     */
    container.addEventListener('submit', async (e) => {
        const form = e.target.closest('form#form-order-table');
        if (!form) return;

        e.preventDefault(); // Prevent default form submission

        // Serialize form data into query parameters
        const formData = new FormData(form);

        // check to prevent bad fetchs
        const orderId = formData.get('order_id').trim();
        if (orderId.length > 0 && !/^\d+$/.test(orderId)) {
            openAlert('Por favor ingrese un número de orden válido.', 'red', 1500);
            return;
        }

        const params = new URLSearchParams(formData).toString();
        await getTabContentAJAX({ container, tabId, params, isPanel: false })

        // clean form after update
        form.querySelector('input').value = ''
    });

    /**
     * Handle changes in the status dropdown.
     * When a select element named 'status' is changed, submit the form automatically.
     */
    container.addEventListener('change', (e) => {
        if (e.target.matches("select[name='status']")) {
            const form = e.target.closest('form');
            if (form) form.requestSubmit(); // Submit the form programmatically
        }
    });
}


/**
 * Loads dynamic tab content via AJAX and inserts it into the specified container.
 * Also initializes the corresponding event handlers for interactive tabs.
 *
 * @async
 * @function getTabContentAJAX
 * @param {Object} options - Configuration object.
 * @param {HTMLElement} options.container - The DOM element where the tab content will be injected.
 * @param {string} options.tabId - The identifier of the tab (used to build the URL and initialize tab-specific logic).
 * @param {string} [options.params=''] - Optional query parameters to append to the URL.
 *
 * @returns {Promise<void>}
 */
async function getTabContentAJAX({ container, tabId, params = '' } = {}) {
    // Construye la URL base reemplazando el nombre del tab
    const base_url = window.TEMPLATE_URLS.profileTabs.replace('{tab_name}', tabId);
    const url = (params) ? `${base_url}?${params}` : base_url;

    try {
        // Realiza la solicitud al servidor
        const response = await fetch(url);
        const data = await response.json();

        // Inicializa eventos específicos según el tab activo
        if (tabId === 'store-data-tab') {
            createTabStore(container, data);
            storeTabEvents(container);

        } else if (tabId === 'users-tab') {
            createTabRoles(container, data);
            usersTabEvents(container, tabId);
            
        } else if (tabId === 'orders-tab') {
            createTabOrders(container, data);
            ordersTabEvents(container, tabId);
        }

    } catch (error) {
        // Manejo de errores en caso de fallo en la carga
        console.error('Error loading content:', error);
        container.innerHTML = '<p>Algo salió mal recargue la página.</p>';
    }
}


/**
 * Initializes the tab interface once the DOM is fully loaded.
 * 
 * - Adds click event listeners to tab buttons to load and display tab content dynamically.
 * - Hides all tab content divs and shows only the selected tab's content.
 * - Fetches tab content via AJAX using the tab's name in the URL.
 * - Calls specific event setup functions based on the active tab.
 * - Automatically triggers a click on the second tab on page load to display its content.
 */
document.addEventListener('DOMContentLoaded', () => {
    
    const contBtnTabs = document.querySelector('.cont-tabs');
    const btnTabs = document.querySelectorAll('.btn-tabs');
    const divTabs = document.querySelectorAll('.tab-content');
    
    contBtnTabs.addEventListener('click', async function (e) {

        const btn = e.target.closest('.btn-tabs');
        if (!btn) return; // Si no se hizo click en un .btn-tabs, ignorar

        // Opcional: evitar repetir acción si ya está activo
        if (btn.classList.contains('active')) return;

        // Remove 'active' class from all tab buttons
        btnTabs.forEach(btn => btn.classList.remove('active'));
        btn.classList.add('active');

        const tabId = btn.dataset.tab;
        const container = document.getElementById(tabId);

        // Hide all tab content divs and show only the selected one
        divTabs.forEach(div => div.style.display = 'none');
        container.style.display = 'block';

        await getTabContentAJAX({ container, tabId })
    })

    const formsClose = document.querySelectorAll('.form-close-profile');
    formsClose.forEach((form) => {
        // this function its from users/widget_login-js
        if (form) widgetUserForms(form, "Close");
    });

    // Automatically trigger click on the second tab to show it on page load
    const firstTab = btnTabs[2];
    if (firstTab) {
        firstTab.click();
        /*
        const tabId = firstTab.dataset.tab;
        const container = document.getElementById(tabId);
        getTabContentAJAX({ container, tabId }) */
    }
});



