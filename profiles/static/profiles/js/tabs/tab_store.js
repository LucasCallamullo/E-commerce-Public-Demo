

/**
 * Generates the initial HTML structure for the Store Data tab,
 * including a form container for store details and containers for
 * shipping and payment methods.
 * 
 * The HTML strings are concatenated and inserted into a temporary
 * container element, then converted into a DocumentFragment for
 * efficient DOM insertion.
 * 
 * @param {number|string} storeId - The identifier of the store, set as a data attribute on the store form.
 * 
 * @returns {Object} An object containing:
 *   - htmlToAppend: A DocumentFragment containing the full HTML structure ready to be appended to the DOM.
 *   - formStore: The DOM element corresponding to the store details form container.
 *   - contShipments: The DOM element container where shipping method forms will be dynamically inserted.
 *   - contPayments: The DOM element container where payment method forms will be dynamically inserted.
 */
function renderTabStoreInit(storeId) {
    const htmlParts = [ 
        /*html*/`<h1 class="bold-main font-xxl">Datos de la Tienda:</h1>`,

        // Container and form for store details
        /*html*/`
            <form class="d-grid cont-grid-122 gap-2 mt-2 mb-2 form-store-grid" 
            data-index="${storeId}"> 
            </form>
        `.trim(),
        
        // Container for Shipping Method forms
        /*html*/`
            <hr class="hr-primary mt-3 mb-1">
            <h2 class="bold-main">Métodos de Envío:</h2>
            <div class="cont-shipments-forms"> </div>
        `.trim(),

        // Container for Payment Method forms
        /*html*/`
            <hr class="hr-primary mt-3 mb-1">
            <h2 class="bold-main">Métodos de Pago:</h2>
            <div class="cont-payments-forms"> </div>
        `.trim(),

        // Informational note displayed below payment methods
        /*html*/`
            <span class="d-flex justify-start align-end mt-2 font-sm">
                <p><b>(*)</b> Cantidad de <b>tiempo en horas</b> hasta cancelar la orden si no sube captura.</p>   
            </span>
        `.trim()
    ];

    // Create a temporary container element and insert the HTML string
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlParts.join('');

    // Retrieve references to key containers for later dynamic insertion
    const formStore = tempDiv.querySelector('.form-store-grid');
    const contShipments = tempDiv.querySelector('.cont-shipments-forms');
    const contPayments = tempDiv.querySelector('.cont-payments-forms');

    // Move the created elements into a DocumentFragment for efficient DOM insertion
    const fragment = document.createDocumentFragment();
    while (tempDiv.firstChild) {
        fragment.appendChild(tempDiv.firstChild);
    }
    
    // Return the fragment and container references for further use
    return { htmlToAppend: fragment, formStore, contShipments, contPayments };
}


/**
 * Renders the store information form inside the specified container element.
 * 
 * The form includes inputs for basic store data (name, address, email, phone)
 * and social media URLs. The provided store object is sanitized via `deepEscape`
 * to prevent XSS or injection issues before inserting values into the form fields.
 * 
 * @param {HTMLElement} container - The DOM element where the store form HTML will be injected.
 * @param {Object} storeObj - The store data object containing fields like:
 *   - name, address, email, cellphone
 *   - ig_url, fb_url, tt_url, wsp_number, google_url, tw_url
 */
function renderStoreForm(container, storeObj) {
    const store = deepEscape(storeObj);
    const formHtml = /*html*/ `
        <label class="d-flex-col gap-1 bolder">
            Datos de la tienda:
            <input type="text" name="name" value="${store.name}">
        </label>
        
        <label class="d-flex-col gap-1 bolder">
            Dirección:
            <input type="text" name="address" value="${store.address}">
        </label>

        <label class="d-flex-col gap-1 bolder">
            E-mail:
            <input type="email" name="email" value="${store.email}">
        </label>
        
        <label class="d-flex-col gap-1 bolder">
            Celular:
            <input type="tel" name="cellphone" value="${store.cellphone}">
        </label>

        <!-- Social Media Links -->
        <h2 class="bold-main mt-2 grid-col-all">Redes Sociales de la Tienda:</h2>

        <label class="d-flex-col gap-1 bolder">
            Instagram:
            <input type="url" name="ig_url" value="${store.ig_url}">
        </label>

        <label class="d-flex-col gap-1 bolder">
            Facebook:
            <input type="url" name="fb_url" value="${store.fb_url}">
        </label>

        <label class="d-flex-col gap-1 bolder">
            TikTok:
            <input type="url" name="tt_url" value="${store.tt_url}">
        </label>

        <label class="d-flex-col gap-1 bolder">
            WhatsApp:
            <input type="tel" name="wsp_number" value="${store.wsp_number}">
        </label>

        <label class="d-flex-col gap-1 bolder">
            Google:
            <input type="url" name="google_url" value="${store.google_url}">
        </label>

        <label class="d-flex-col gap-1 bolder">
            Twitter/X:
            <input type="url" name="tw_url" value="${store.tw_url}">
        </label>

        <div class="grid-col-all d-flex justify-center align-center">
            <button class="btn gap-2 btn-40 h-min w-min px-2 py-1 btn-alt bolder text-truncate" type="submit">
                <i class="ri-save-3-line font-xl fw-normal"></i>
                <span class="text-truncate">Guardar Cambios</span>
            </button>
        </div>
    `.trim();

    container.innerHTML = formHtml;
}


/**
 * Renders a list of shipment method forms inside the specified container.
 * 
 * Each shipment method is displayed as an individual form with fields for:
 * - Name (disabled input)
 * - Price (editable input, formatted with thousands separator)
 * - Active status (checkbox)
 * - Description (textarea)
 * 
 * The shipment data is sanitized with `deepEscape` to avoid XSS vulnerabilities.
 * The generated forms are inserted all at once into the container’s innerHTML.
 * 
 * @param {HTMLElement} container - The DOM element where shipment forms will be injected.
 * @param {Array<Object>} shipments - Array of shipment method objects, each with:
 *   - id: Unique identifier
 *   - name: Shipment method name
 *   - price: Numeric price value
 *   - is_active: Boolean indicating if active
 *   - description: Text description
 */
function renderStoreFormShipments(container, shipments) {
    const formsHtml = shipments.map(ship => {
        const shipment = deepEscape(ship); // Sanitize data
        const price = formatNumberWithPoints(shipment.price, true);
        return /*html*/`
            <form class="shipments-form mt-2 mb-2" data-index="${shipment.id}">
                <label class="d-flex-col gap-1 bolder">
                    Nombre:
                    <input type="text" value="${shipment.name}" disabled>
                </label>

                <label class="d-flex-col gap-1 bolder">
                    Precio:
                    <input type="price" name="price" value="${price}">
                </label>

                <label class="d-flex-col gap-1 bolder">
                    Activo:
                    <input class="text-center" type="checkbox" name="is_active" ${shipment.is_active ? 'checked' : ''}>
                </label>

                <label class="d-flex-col gap-1 bolder">
                    Descripción:
                    <textarea class="btn-48 w-100 p-1" name="description">${shipment.description}</textarea>
                </label>

                <div class="d-flex-col align-end justify-end gap-1">
                    <button class="btn btn-36 w-100 btn-alt bolder" type="submit"> 
                        <i class="ri-edit-box-line font-lg fw-normal"></i>
                        Editar
                    </button>
                </div>
            </form>
        `;
    }).join('');

    container.innerHTML = formsHtml;
}


/**
 * Renders a list of payment method forms inside the specified container.
 * 
 * Each payment method is displayed as an individual form with fields for:
 * - Name (disabled input)
 * - Time (editable input)
 * - Active status (checkbox)
 * - Description (textarea)
 * 
 * The payment data is sanitized with `deepEscape` to avoid XSS vulnerabilities.
 * The generated forms are inserted all at once into the container’s innerHTML.
 * 
 * @param {HTMLElement} container - The DOM element where payment forms will be injected.
 * @param {Array<Object>} payments - Array of payment method objects, each with:
 *   - id: Unique identifier
 *   - name: Payment method name
 *   - time: String representing time (e.g. hours until order cancellation)
 *   - is_active: Boolean indicating if active
 *   - description: Text description
 */
function renderStoreFormPayments(container, payments) {
    const formsHtml = payments.map(paym => {
        const payment = deepEscape(paym); // Sanitize data
        return /*html*/`
            <form class="payments-form mt-2 text-mobile" data-index="${payment.id}">
                <label class="d-flex-col gap-1 bolder">
                    Nombre:
                    <input type="text" value="${payment.name}" disabled>
                </label>
                <label class="d-flex-col gap-1 bolder">
                    Tiempo(*)
                    <input type="text" name="time" value="${payment.time}">
                </label>
                <label class="d-flex-col gap-1 bolder">
                    Activo:
                    <input type="checkbox" name="is_active" ${payment.is_active ? 'checked' : ''}>
                </label>
                <label class="d-flex-col gap-1 bolder">
                    Descripción:
                    <textarea class="btn-48 w-100 p-1" name="description">${payment.description}</textarea>
                </label>
                <div class="d-flex-col align-end justify-end gap-1">
                    <button class="btn btn-36 w-100 btn-alt bolder" type="submit"> 
                        <i class="ri-edit-box-line font-lg fw-normal"></i>
                        Editar
                    </button>
                </div>
            </form>
        `;
    }).join('');

    container.innerHTML = formsHtml;
}


/**
 * Creates and renders the store tab content inside a specified container.
 * 
 * This function initializes the store tab HTML structure on first call,
 * rendering the main store form, shipment methods forms, and payment methods forms.
 * On subsequent calls, it updates the existing rendered forms with new data.
 * 
 * @param {HTMLElement} container - The DOM element where the store tab content will be rendered.
 * @param {Object} data - The data object containing store information and related methods.
 *   Expected properties:
 *     - store: Object containing store details (e.g. id, name, address, etc.).
 *     - shipments: Array of shipment method objects.
 *     - payments: Array of payment method objects.
 */
function createTabStore(container, data) {
    if (!container._hasInit) {
        // Generate base HTML structure and retrieve relevant sub-containers
        const { htmlToAppend, formStore, contShipments, contPayments } = renderTabStoreInit(data.store.id);
        
        // Render the main store form with store data
        renderStoreForm(formStore, data.store);

        // Render shipment methods forms
        renderStoreFormShipments(contShipments, data.shipments);

        // Render payment methods forms
        renderStoreFormPayments(contPayments, data.payments);

        // Append the generated fragment to the container
        container.appendChild(htmlToAppend);
        container._hasInit = true;
        return;
    }

    // On subsequent calls, update only the forms inside the existing container
    const formStore = container.querySelector('.form-store-grid');
    const contShipments = container.querySelector('.cont-shipments-forms');
    const contPayments = container.querySelector('.cont-payments-forms');

    renderStoreForm(formStore, data.store);
    renderStoreFormShipments(contShipments, data.shipments);
    renderStoreFormPayments(contPayments, data.payments);
}

