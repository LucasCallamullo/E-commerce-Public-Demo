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
    // Crear todo el HTML como un único string
    const html = /*html*/`
        <h2 class="bold-main justify-self-center mt-3 mb-2 font-xxl">Lista de Pedidos</h2>

        <!-- If user is admin, add the filter form including search input and status select -->
        ${isAdmin ? /*html*/`
            <form class="d-flex-col-row justify-center align-center gap-2 mt-1" id="form-order-table">
                <strong class="bold-main">Filtrar por N° Orden:</strong>
                <div class="cont-user-search">
                    <input type="search" name="order_id" value='' placeholder="Buscar N° Orden...">
                    <button class="btn" type="submit">
                        <i class="ri-price-tag-3-line font-lg search-icon"></i>
                    </button>
                </div>
                <select class="w-min select-orders" name="status"></select>
            </form>
        ` : ''}

        <!-- Add an empty container where the orders table will be rendered dynamically -->
        <div class="d-grid cont-header-orders mt-4 bolder font-md"></div>
        <div class="d-grid cont-table-orders bolder font-md"></div>
    `;

    // Create a temporary container element and insert the HTML string
    const t = document.createElement('div');
    t.innerHTML = html.trim().replace(/<!--[\s\S]*?-->/g, '');

    // sirve para incluir todos los nodos dentro de fragment en lugar de encerrar todo en un 
    // div contenedor de todo e insertarlo como unico child
    const fragment = document.createDocumentFragment();
    fragment.append(...t.childNodes)
    // while (t.firstChild) fragment.appendChild(tempDiv.firstChild);    //tmb valido
    
    // Return the temporary container and the orders container element
    return { htmlToAppend: fragment };
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
function renderOrderTable(tableCont, tableHeader, orders, isAdmin) {
    const hasOrders = (orders.length > 0);
    let tableRows = '';

    if (hasOrders) {
        // Create table header add column only for admin
        tableHeader.innerHTML = /*html*/`
            <b class="text-break text-secondary ver-order">Orden</b>
            <b class="text-break text-secondary d-desktop-block">Fecha</b>
            <b class="text-break text-secondary">Estado</b>
            <b class="text-break text-secondary">Resumen</b>
            ${(isAdmin) ? /*html*/`<b class="text-break text-secondary d-desktop-block">Captura</b>`: ''}
        `.trim();

        // Create table rows for each order
        const tableHtml = orders.map(ord => {
            const order = deepEscape(ord); // Basic front-end sanitization
            const url = window.TEMPLATE_URLS.orderDetail.replace('{order_id}', `${order.id}`);
            const dateFormat = shortDate(`${order.created_at}`);
            return /*html*/`
                <a class="row-order bold-main ver-order underline-anim" href="${url}">
                    <span>#${order.id}&nbsp;</span>
                </a>
                <div class="row-order bolder d-desktop-block">${dateFormat}</div>
                <div class="row-order bold-orange text-truncate">${order.status_name}</div>
                <div class="row-order bolder">$ ${formatNumberWithPoints(order.total)}</div>

                ${(isAdmin) ? /* columna extra agregada para admin bajar capturas */ /*html*/`
                    <a class="row-order bold-main underline-anim d-desktop-block" 
                    href="${url}" 
                    target="_blank"
                    rel="noopener noreferrer">
                        <span>Descargar</span>
                    </a>
                `: ''}
            `;
        }).join('');

        tableRows += tableHtml.trim().replace(/<!--[\s\S]*?-->/g, '');
    } else {
        // If no orders, show a friendly message with a link to browse products
        const url = window.TEMPLATE_URLS.productList;
        const tableRow = (isAdmin) ? /*html*/`
            <h2 class="grid-col-all mt-1 text-break font-lg ver-order">No hay ordenes.</h2>
            <p class="grid-col-all mt-3 mb-2 text-break font-md ver-order"> 
                Por favor elija otro filtro de estado para buscar ordenes.
            </p>
        `: /*html*/`
            <h2 class="grid-col-all mt-1 text-break font-lg ver-order">Todavía no hay ordenes.</h2>
            <h3 class="grid-col-all text-break font-md ver-order">Mira nuestros productos:</h3>
            <div class="grid-col-all justify-self-center mb-4">
                <a href="${url}" class="w-min text-truncate btn btn-main gap-2 px-2 py-1 bolder font-md">
                    <i class="ri-shopping-cart-2-line fw-normal font-lg"></i>Todos nuestros productos
                </a>
            </div>
        `;
        tableRows += tableRow.trim();
    }

    // Insert and replace with the generated HTML directly into the container
    tableCont.innerHTML = tableRows;
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


    const render = (cont, isAdmin) => {
        // Get reference to the container where orders will be rendered later
        const tableCont = cont.querySelector('.cont-table-orders');
        const tableHeader = cont.querySelector('.cont-header-orders');
        const containerSelect = cont.querySelector('.select-orders');

        if (tableCont) renderOrderTable(tableCont, tableHeader, data.orders || [], isAdmin);

        if (containerSelect) {
            // if is null get 2, default
            renderOrderSelect(containerSelect, data.status_orders || [], data.status_id || 2); 
        }
    }

    // container.innerHTML = ''; // Clear the container before rendering
    if (!container._hasInit) {
        // Generate base HTML structure
        const { htmlToAppend } = renderOrderTabInit(data.is_admin || false);

        render(htmlToAppend, data.is_admin || false);
        container.appendChild(htmlToAppend); // Append the fragment to the container
        container._hasInit = true;
        return;
    }

    render(container, data.is_admin || false);
}

