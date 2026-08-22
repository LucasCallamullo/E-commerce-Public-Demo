/// <reference path="../../../../../static/js/base.js" />
/// <reference path="../../../../../static/js/utils.js" />
/// <reference path="../../../../../favorites/static/favorites/js/add_favorites.js" />
/// <reference path="../../../../../products/static/products/js/logic/product_store.js" />


/**
 * Fetches a product list using the current filters and updates the product view.
 * 
 * @param {Object} dictAdd - Additional filters to apply (overrides base filters).
 * @param {boolean} activeCounter - Whether to update browser history and navigation counter.
 */
let counterNavigating = 0;
async function fetchProductList(dictAdd, activeCounter = true) {
    // 1. Get all current filters from hidden inputs
    const filtersCont = document.getElementById('form-filters');
    const filterInputs = filtersCont.querySelectorAll('input[type="hidden"]');

    // 2. Build a base dictionary with filter values from the DOM
    const dictBase = {};
    filterInputs.forEach(input => {
        if (input.value) dictBase[input.name] = input.value;
    });

    // 3. Merge additional filters (overriding existing ones if needed)
    Object.assign(dictBase, dictAdd);

    // 4. Create URLSearchParams from the combined filter dictionary
    const params = new URLSearchParams(dictBase);

    const url = `${window.TEMPLATE_URLS.productList}?${params.toString()}`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Search failed');
        const data = await response.json();

        // Update product container and product data
        const contProducts = document.getElementById('cont-product-cards');

        // setear nueva lista del fetch
        window.PRODUCT_STORE.setData(data.products);
        
        console.log(data.products)

        // actualizar vista de lista de cartas
        updateProductListCards(contProducts, data.products, data);

        // actualizas vista de botones
        updateContPagination(data.pagination)

        // actualizar marcas
        updateContBrands(contProducts);
        updateContPrices(contProducts);

        // hacer movimiento visual al nuevo grupo de tarjetas
        scrollToSection(contProducts, 'highlight-main');

        // Only update URL and counter if not triggered from browser navigation
        if (activeCounter) { 
            const queryString = `?${params.toString()}`;
            history.pushState(null, '', queryString);
            counterNavigating++;
        }

    } catch (error) {
        console.error('Error:', error);
    }
}


/**
 * Updates the pagination UI and the results range text based on
 * pagination metadata returned by the backend.
 *
 * This function supports two modes:
 *
 * 1) SSR mode:
 *    When `pagination` is null, pagination data is read from
 *    data attributes on the pagination container:
 *
 *    - data-total-pages: total number of available pages
 *    - data-page-num: currently active page
 *
 * 2) CSR / API mode:
 *    When a `pagination` object is provided, the pagination UI
 *    and the results range text are recalculated dynamically
 *    using backend-provided metadata.
 *
 * Expected pagination object structure:
 * {
 *   page: number,              // Current page (1-based)
 *   page_size: number,         // Maximum number of results per page
 *   total_pages: number,       // Total number of pages
 *   results_on_page: number,   // Number of results returned for this page
 *   total_results: number      // Total number of results available
 * }
 *
 * @param {Object|null} pagination - Pagination metadata from the backend,
 *                                   or null when using SSR data attributes.
 */
function updateContPagination(pagination = null) {

    const container = document.getElementById('cont-pagination');

    let totalPages, pageNum;
    if (pagination == null) {
        totalPages = parseInt(container.dataset.totalPages); // Total number of pages
        pageNum = parseInt(container.dataset.pageNum);       // Current page
    } else {
        totalPages = parseInt(pagination.total_pages);
        pageNum = parseInt(pagination.page);
        
        // buscar si es mayor el resultado o el tamaño real del total por pagina 
        const pageSize = parseInt(pagination.page_size);
        const start = (pageNum > 0) ? (pageNum - 1) * pageSize + 1 : 0;
        const end = Math.min(pageNum * pageSize, parseInt(pagination.total_results));
        // actualiza el span text para ux
        const s = document.getElementById('span-results-page');
        s.textContent = `Mostrando (${start} - ${end}) de ${pagination.total_results} resultados`;
    }

    container.innerHTML = '';

    // Generate a button for each page number
    for (let num = 1; num <= totalPages; num++) {
        const btn = document.createElement('button');
        btn.className = 'btn btn-28 border-hover bolder btn-page';

        // Highlight the current page with a special class
        if (num === pageNum) btn.classList.add('border-main');
        btn.dataset.number = num;
        btn.innerHTML = `${num}`;
        container.appendChild(btn);
    }

    // Attach event listener only once using a flag
    if (!container._hasEvent) {
        container.addEventListener('click', (e) => {
            const btn = e.target.closest('button.btn-page');

            // Ignore clicks on the active page button or non-buttons
            if (!btn || btn.classList.contains('border-main')) return;

            // Remove highlight from previously active button
            const exBtnMain = container.querySelector('.border-main');
            if (exBtnMain) exBtnMain.classList.remove('border-main');

            // Highlight the newly selected page
            btn.classList.add('border-main');

            // Extract page number and trigger product fetch
            const num = btn.dataset.number;
            fetchProductList({ page: num });
        });

        // Mark container as initialized to avoid duplicate listeners
        container._hasEvent = true;
    }
}


/**
 * Handles the browser's back/forward navigation (popstate event).
 * 
 * This function sets up an event listener for the `popstate` event, which is triggered
 * when the user navigates through the browser history (e.g., using the back or forward buttons).
 * 
 * When triggered, it performs the following actions:
 * 
 * 1. Checks if the `counterNavigating` is greater than 0 to avoid redundant fetches.
 * 2. Parses the current URL parameters from `window.location.search`.
 * 3. Calls `fetchProductList(params, false)` to update the product list without pushing a new state.
 * 4. Decrements the `counterNavigating` to track user-driven navigation.
 * 5. Updates the pagination buttons UI to visually reflect the current page.
 * 
 * Note: This function should be called once to initialize the listener.
 * It assumes that `counterNavigating` is defined in the global scope
 * and that `fetchProductList` is a function responsible for fetching and rendering products.
 */
function historyPopState() {
    window.addEventListener('popstate', () => {
        if (counterNavigating > 0) {
            const params = Object.fromEntries(new URLSearchParams(window.location.search).entries());
            fetchProductList(params, false);
            counterNavigating--;

            // Update pagination button styles to reflect the active page
            const container = document.getElementById('cont-pagination');
            const btns = container.querySelectorAll('.btn-page');
            const currentPage = params.page || '1';
            btns.forEach(btn => {
                btn.classList.remove('border-main');
                if (btn.dataset.number === currentPage) btn.classList.add('border-main');
            });
        }
    });
}
