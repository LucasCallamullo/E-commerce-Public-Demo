/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../products/static/products/js/components/cards_products.js" />
/// <reference path="../../../../products/static/products/js/logic/cards_products.js" />
/// <reference path="../../../../products/static/products/js/components/carousel_products.js" />
/// <reference path="../../../../profiles/static/profiles/js/tabs/tab_orders.js" />


function initSwiperFavorites () { 
    // el nombre de la clase  es el que define a que swiper corresponde esta config
    const swiper = new Swiper(`#swiper-favs`, {
        loop: true, // Evita acumulación de slides mal posicionados
        autoplay: {
            delay: 6000,
            disableOnInteraction: false,
        },
        slidesPerView: "auto", // Se ajusta con el CSS
        centeredSlides: false, // Evita que los slides se centren incorrectamente
        grabCursor: true,
        navigation: {
            nextEl: `#next-fav`,
            prevEl: `#prev-fav`,
        },
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
            createCarouselCards(container, data.products);

        } else if (tabId === 'invoices-tab') {
            createTabOrders(container, data);

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
        if (btn.classList.contains('active-tab')) return;

        // Remove 'active' class from all tab buttons
        btnTabs.forEach(btn => btn.classList.remove('active-tab'));
        btn.classList.add('active-tab');

        const tabId = btn.dataset.tab;
        const container = document.getElementById(tabId);

        // Hide all tab content divs and show only the selected one
        divTabs.forEach(div => div.style.display = 'none');
        container.style.display = 'block';

        await getTabContentAJAX({ container, tabId })
    })

    // form to close session with drf api
    const formsClose = document.querySelectorAll('.form-close-profile');
    formsClose.forEach((form) => {
        if (form) widgetUserForms(form, "Close");
    });

    // Automatically trigger click on the second tab to show it on page load
    const firstTab = btnTabs[1];
    if (firstTab) {
        firstTab.click();
    }
});


