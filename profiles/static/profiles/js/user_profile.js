/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../static/js/overlay_modal.js" />
/// <reference path="../../../../users/static/users/js/widget_login.js" />
/// <reference path="../../../../products/static/products/js/components/cards_products.js" />
/// <reference path="../../../../products/static/products/js/logic/cards_products.js" />
/// <reference path="../../../../products/static/products/js/logic/product_store.js" />
/// <reference path="../../../../products/static/products/js/components/carousel_products.js" />
/// <reference path="../../../../profiles/static/profiles/js/tabs/tab_orders.js" />


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
 * @param {boolean} [options.isPanel=true] - Indicates whether tab-specific event setup should be run.
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
        if (tabId === 'orders-tab') {
            createTabOrders(container, data);
        }
        else if (tabId === 'favorites-tab') {
            // All logic below depends on carousel_cards and related functions from that module
            // necesarias listas globales auxiliares en memoria js para hacer busquedas filtros desde
            // window.PRODUCT_STORE. y obtener valores asociados con mejor performance por filtros
            CATALOG_MODAL_STORE.setCatalog(data.categories || [], data.brands || []);
            PRODUCT_MODAL_STORE.setData(data.products || []);
            createTabfavorites(container, PRODUCT_MODAL_STORE.getData());

        } else if (tabId === 'invoices-tab') {
            createTabInvoices(container, data);
        }

    } catch (error) {
        // Manejo de errores en caso de fallo en la carga
        console.error('Error loading content:', error);
        container.innerHTML = /*html*/`<p>Algo salió mal recargue la página.</p>`;
    }
}


/**
 * Initializes the tab navigation system.
 *
 * - Handles click events on tab buttons using event delegation.
 * - Prevents unnecessary reloads when clicking the active tab.
 * - Toggles the "active-tab" class between buttons.
 * - Shows the selected tab content and hides the rest.
 * - Loads tab content asynchronously via AJAX.
 * - Automatically opens the second tab on page load.
 */
function initTabs() {
    const contBtnTabs = document.querySelector('.cont-tabs');
    if (!contBtnTabs) return;

    const btnTabs = contBtnTabs.querySelectorAll('.btn-tabs');
    const divTabs = document.querySelectorAll('.tab-content');

    contBtnTabs.addEventListener('click', async (e) => {
        const btn = e.target.closest('.btn-tabs');

        // Optional: prevent reloading if the tab is already active
        if (!btn || btn.classList.contains('active-tab')) return;

        // Remove 'active-tab' class from all buttons
        btnTabs.forEach(b => b.classList.remove('active-tab'));
        btn.classList.add('active-tab');

        const tabId = btn.dataset.tab;
        const container = document.getElementById(tabId);

        // Hide all tab content containers and show only the selected one
        divTabs.forEach(div => div.style.display = 'none');
        container.style.display = 'block';

        // Fetch and render tab content dynamically
        await getTabContentAJAX({ container, tabId });
    });

    // Automatically trigger click on the second tab on page load
    btnTabs[1]?.click();
}


/**
 * Entry point for page-specific JavaScript.
 * Initializes all UI modules once the DOM is fully loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    // events in endpoints / users_edit.js
    initLogoutForm();
    initEditUserForm();
});

