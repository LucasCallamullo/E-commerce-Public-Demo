/// <reference path="../../../../../static/js/base.js" />
/// <reference path="../../../../../static/js/utils.js" />


/**
 * Generates the base HTML structure for the "Invoices" tab and returns it as a DocumentFragment.
 *
 * This includes the heading and empty containers for the table header and rows.
 *
 * @returns {Object} - An object containing:
 *   - htmlToAppend {DocumentFragment}: The fragment containing the base HTML elements.
 */
function renderInvoiceTabInit() {
    // Create the base HTML as a single string
    const html = /*html*/`
        <h2 class="bold-main justify-self-center mt-3 mb-2 font-xxl">Lista de Pagos</h2>

        <!-- Add an empty container where the orders table will be rendered dynamically -->
        <div class="d-grid cont-header-payments mt-4 bolder font-md"></div>
        <div class="d-grid cont-table-payments bolder font-md"> </div>
    `.trim().replace(/<!--[\s\S]*?-->/g, '');

    // Create a temporary container element and insert the HTML string
    const t = document.createElement('div');
    t.innerHTML = html;

    // Move all child nodes into a DocumentFragment to avoid extra wrapper nodes
    const fragment = document.createDocumentFragment();
    fragment.append(...t.childNodes);
    
    // Return the fragment to be appended later
    return { htmlToAppend: fragment };
}


/**
 * Renders the invoice table inside the given container.
 *
 * This function generates the table header and rows based on the provided invoices array.
 * If there are no invoices, it displays a friendly message linking to the product list.
 *
 * @param {HTMLElement} tableCont - The container element where invoice rows will be inserted.
 * @param {HTMLElement} tableHeader - The container element for the table header.
 * @param {Array} invoices - Array of invoice objects to render in the table.
 */
function renderInvoiceTable(tableCont, tableHeader, invoices) {
    const hasOrders = (invoices.length > 0);
    let tableRows = '';

    if (hasOrders) {
        // Create table header
        tableHeader.innerHTML = /*html*/`
            <b class="text-break text-secondary ver-order">Factura</b>
            <b class="text-break text-secondary d-desktop-block">Fecha</b>
            <b class="text-break text-secondary">Método</b>
            <b class="text-break text-secondary">Total</b>
            <b class="text-break text-secondary d-desktop-block">Factura</b>
        `.trim();
    
        // Create table rows for each invoice
        const tableHtml = mockInvoices.map(inv => {
            const invoice = deepEscape(inv); // Basic front-end sanitization
            const url = window.TEMPLATE_URLS.orderDetail.replace('{order_id}', `${invoice.order_id}`);
            const dateFormat = shortDate(`${invoice.updated_at}`);
            return /*html*/`
                <a class="row-order bold-main underline-anim ver-order" href="${url}">
                    <span>#${invoice.id}&nbsp;</span>
                </a>
                <div class="row-order bolder d-desktop-block">${dateFormat}</div>
                <div class="row-order text-truncate">
                    ${invoice.payment_method}
                </div>
                <div class="row-order bolder ${(invoice.is_paid) ? 'bold-red' : 'bold-green'}">
                    ${(invoice.is_paid) ? 'Devolución' : `$ ${formatNumberWithPoints(invoice.fiscal_total)}` }
                </div>
                <a class="row-order bold-main underline-anim d-desktop-block" href="${url}">
                    <span>Descargar</span>
                </a>
            `;
        }).join('');

        tableRows += tableHtml.trim().replace(/<!--[\s\S]*?-->/g, '');
    } else {
        // If no invoices, show a friendly message with a link to browse products
        const url = window.TEMPLATE_URLS.productList;
        const tableRow = /*html*/`
            <h2 class="grid-col-all mt-1 text-break ver-order font-lg">Todavía no hay Pagos Realizados.</h2>
            <p class="grid-col-all text-break ver-order font-md">Mira nuestros productos:</p>
            <div class="grid-col-all justify-self-center mb-4">
                <a href="${url}" class="w-min text-truncate btn btn-main gap-2 px-2 py-1 bolder font-md">
                    <i class="ri-shopping-cart-2-line fw-normal font-lg"></i>Todos nuestros productos
                </a>
            </div>
        `.trim();
        tableRows += tableRow;
    }

    // Insert the generated rows into the container
    tableCont.innerHTML = tableRows;
}


/**
 * Initializes and renders the "Invoices" tab inside a given container.
 * 
 * This function handles both the **initial render** and subsequent updates:
 * - On the first call, it generates the base HTML structure and appends it.
 * - On subsequent calls, it only updates the invoice table without re-creating the base structure.
 *
 * @param {HTMLElement} container - The DOM element where the invoices tab should be rendered.
 * @param {Object} data - The data object containing information for rendering.
 * @param {boolean} data.is_admin - Flag indicating if the current user is an admin.
 * @param {Array} data.invoices - Array of invoice objects to populate the table.
 */
function createTabInvoices(container, data) {

    /**
     * Render the invoice table inside the provided container.
     *
     * @param {HTMLElement} cont - The container element holding the invoice table elements.
     */
    const render = (cont) => {
        // Get references to the table container and header elements
        const tableCont = cont.querySelector('.cont-table-payments');
        const tableHeader = cont.querySelector('.cont-header-payments');

        // Render the invoice table if the container exists
        if (tableCont) renderInvoiceTable(tableCont, tableHeader, data.invoices || []);
    }

    // Only run initialization once per container
    if (!container._hasInit) {
        // Generate the base HTML structure for the invoices tab
        const { htmlToAppend } = renderInvoiceTabInit(data.is_admin || false);

        // Render the invoices into the table container inside the fragment
        render(htmlToAppend);

        // Append the entire fragment to the main container
        container.appendChild(htmlToAppend);

        // Mark the container as initialized to prevent re-initialization
        container._hasInit = true;
        return;
    }

    // After the first render, only update the existing invoice table
    render(container);
}
