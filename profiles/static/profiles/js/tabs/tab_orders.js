/// <reference path="../../../../../static/js/base.js" />
/// <reference path="../../../../../static/js/utils.js" />


/**
 * Generates the initial HTML structure for the orders tab,
 * including the filter form (if admin) and an empty container for the orders table.
 * 
 * This function creates the HTML as a string, inserts it into a temporary DOM element,
 * and returns the element to be appended as well as the container element where orders
 * will be dynamically rendered later.
 * 
 *  @param {boolean} isAdmin: from data.is_admin - Whether the current user is an admin.
 * 
 * @returns {Object} An object containing:
 *   - htmlToAppend: The temporary container (`div`) element with the generated HTML.
 *   - containerTable: The DOM element inside `htmlToAppend` where the orders will be rendered dynamically.
 *   - containerSelect: The DOM element inside `htmlToAppend` where the orders stauts will be rendered dynamically.
 */
function renderOrderTabInit(isAdmin) {

    const htmlParts = [
        /*html*/`<h1 class="bold-main mt-1 mb-2 font-xxl">Lista de Pedidos</h1>`,

        // If user is admin, add the filter form including search input and status select
        isAdmin ? /*html*/`
            <form class="d-flex-col-row justify-center align-center gap-2 mt-1 mb-3" id="form-order-table">
                <strong class="bold-main">Filtrar por N° Orden:</strong>
                <div class="cont-user-search">
                    <input type="search" name="order_id" value='' placeholder="Buscar N° Orden...">
                    <button class="btn" type="submit">
                        <i class="ri-price-tag-3-line font-lg search-icon"></i>
                    </button>
                </div>
                <select class="w-min select-orders" name="status"></select>
            </form>
        `.trim() : '',

        // Add an empty container where the orders table will be rendered dynamically
        /*html*/`<div class="d-grid cont-table-orders mt-2 bolder font-md"></div>`
    ];

    // Create a temporary container element and insert the HTML string
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlParts.join('');

    // Get reference to the container where orders will be rendered later
    const containerTable = tempDiv.querySelector('.cont-table-orders');
    const containerSelect = tempDiv.querySelector('.select-orders');

    const fragment = document.createDocumentFragment();
    while (tempDiv.firstChild) {
        fragment.appendChild(tempDiv.firstChild);
    }
    
    // Return the temporary container and the orders container element
    return { htmlToAppend: fragment, containerTable, containerSelect };
}


/**
 * Renders the orders table content inside a specified container.
 * 
 * This function clears the container and dynamically creates the table header and
 * the rows for each order. If there are no orders, it displays a message inviting
 * the user to browse products.
 * 
 * @param {HTMLElement} container - The DOM element where the orders table content will be rendered.
 * @param {Array<Object>} orders - Array of order objects to be displayed in the table.
 *   Each order object is expected to contain at least:
 *     - id: The order ID.
 *     - created_at: The creation date string of the order.
 *     - total: The total amount of the order.
 *     - status__name: The status name of the order.
 */
function renderOrderTable(container, orders) {
    const hasOrders = (orders.length > 0);
    let tableRows = '';

    if (hasOrders) {
        // Create table header
        tableRows += /*html*/`
            <b class="text-center text-break text-secondary">Orden</b>
            <b class="text-start text-break text-secondary d-desktop-block">Fecha</b>
            <b class="text-center text-break text-secondary">Estado</b>
            <b class="text-center text-break text-secondary">Resumen</b>
            <b class="text-start text-break text-secondary d-desktop-block">Factura</b>
        `.trim();

        // Create table rows for each order
        const tableHtml = orders.map(ord => {
            const order = deepEscape(ord); // Basic front-end sanitization
            const url = window.TEMPLATE_URLS.orderDetail.replace('{order_id}', `${order.id}`);
            const dateFormat = shortDate(`${order.created_at}`);
            return /*html*/`
                <a class="text-center row-order bold-main underline-anim" 
                    href="${url}"># ${order.id}
                </a>
                <div class="text-start row-order bolder d-desktop-block">${dateFormat}</div>
                <div class="text-center row-order bold-orange text-truncate">${order.status__name}</div>
                <div class="text-center row-order bolder">$ ${order.total}</div>
                <a class="text-start row-order bold-main underline-anim d-desktop-block" href="${url}">
                    Ver Orden
                </a>
            `;
        }).join('');

        tableRows += tableHtml;
    } else {
        // If no orders, show a friendly message with a link to browse products
        const url = window.TEMPLATE_URLS.productList;
        const tableRow = /*html*/`
            <h3 class="grid-col-all mt-1 text-break font-lg">Todavía no hay ordenes.</h3>
            <h4 class="grid-col-all text-break font-md">Mira nuestros productos:</h4>
            <div class="grid-col-all justify-self-center">
                <a href="${url}" class="w-min text-truncate btn btn-main gap-2 px-2 py-1 bolder font-md">
                    <i class="ri-shopping-cart-2-line fw-normal font-lg"></i>Todos nuestros productos
                </a>
            </div>
        `.trim();
        tableRows += tableRow;
    }

    // Insert and replace with the generated HTML directly into the container
    container.innerHTML = tableRows;
}

/**
 * Renders a <select> element's options based on a list of order statuses.
 * 
 * Elegantly builds the HTML by:
 * 1. Using `map()` to transform each object in `ordersStatus` into an HTML <option> string.
 * 2. Using `join('')` to combine all strings into a single HTML block without separators.
 * 3. Assigning the final HTML string to `container.innerHTML` in one go, avoiding manual concatenation.
 *
 * @param {HTMLElement} container - The <select> element where options will be rendered.
 * @param {Array<Object>} ordersStatus - List of status objects, each with `id` and `name` properties.
 * @param {number|string} statusId - The ID of the currently selected status.
 */
function renderOrderSelect(container, ordersStatus, statusId) {
    // Generate all option tags in one line using map + join
    const newOptions = ordersStatus.map(oStatus => /*html*/`
        <option value="${oStatus.id}" ${oStatus.id == statusId ? 'selected' : ''}>
            ${oStatus.name}
        </option>
    `).join('');

    // Insert and replace the final HTML into the container
    container.innerHTML = newOptions;
}


/**
 * Creates and renders the orders table inside a given container element.
 * 
 * This function clears the container content, generates the base HTML structure for the orders tab,
 * fills the orders table with order data, and appends the result to the container.
 * 
 * @param {HTMLElement} container - The DOM element where the orders table will be inserted.
 * @param {Object} data - The data object containing orders and status information.
 *   Expected properties:
 *     - orders: Array of order objects to be rendered in the table.
 *     - is_admin: Boolean indicating if the current user is an admin (to show filters).
 *     - status_orders: Array of status objects used to populate the status filter select.
 *     - status_id: The currently selected status id (optional).
 */
function createTabOrders(container, data) {
    // container.innerHTML = ''; // Clear the container before rendering
    if (!container._hasInit) {
        // Generate base HTML structure
        const { htmlToAppend, containerTable, containerSelect } = renderOrderTabInit(data.is_admin || false);
        
        // Render the orders inside the table container
        if (containerTable) renderOrderTable(containerTable, data.orders || []);
        if (containerSelect) {
            // if is null get 2, default
            renderOrderSelect(containerSelect, data.status_orders || [], data.status_id || 2); 
        }

        container.appendChild(htmlToAppend); // Append the fragment to the container
        container._hasInit = true;
        return;
    }

    // after the first render only refill this containers
    const containerTable = container.querySelector('.cont-table-orders');
    const containerSelect = container.querySelector('.select-orders');
    if (containerTable) renderOrderTable(containerTable, data.orders || []);
    if (containerSelect) {
        // if is null get 2, default
        renderOrderSelect(containerSelect, data.status_orders || [], data.status_id || 2); 
    }
}

