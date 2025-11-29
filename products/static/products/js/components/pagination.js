/// <reference path="../../../../../static/js/base.js" />
/// <reference path="../../../../../static/js/utils.js" />
/// <reference path="../../../../../favorites/static/favorites/js/add_favorites.js" />


window.ProductStore = {
    data: [],
    setData(newData) {
        /**
         * Sets the internal product data store.
         *
         * @param {Array} newData - An array of product objects to be stored.
         */
        this.data = newData;
    },
    getData() {
        /**
         * Returns the current product data.
         *
         * @returns {Array} - The array of stored product objects.
         */
        return this.data;
    },


    getPriceRange() {
        /**
         * Calculates the minimum and maximum prices from the product list,
         * taking into account any applicable discount on each product.
         * Caches the result until data is updated.
         * 
         * @returns {Object} An object with the `min` and `max` prices (both rounded down).
         */
        if (!this.data.length) return { min: 0, max: 0 };

        let minPrice = Infinity;
        let maxPrice = -Infinity;

        for (const p of this.data) {
            const price = parseFloat(p.price);
            const discount = p.discount;

            const finalPrice = discount > 0
                ? price - (price * (discount / 100))
                : price;

            if (finalPrice < minPrice) minPrice = finalPrice;
            if (finalPrice > maxPrice) maxPrice = finalPrice;
        }

        return {
            min: Math.floor(minPrice),
            max: Math.floor(maxPrice),
        };
    },
    filterByPrice(min, max) {
        /**
         * Filters the list of products based on a minimum and maximum price range.
         * Takes into account the discount of each product to calculate the final price.
         * 
         * @param {number} min - The minimum price allowed (inclusive).
         * @param {number} max - The maximum price allowed (inclusive).
         * @returns {Array<Object>} An array of products whose final price is within the given range.
         */
        return this.data.filter(p => {
            // Calculate discount if applicable
            const finalPrice = p.discount > 0 
                ? p.price - (p.price * (p.discount / 100)) 
                : p.price;

            // Check if the final price is within the given range (inclusive)
            return finalPrice >= min && finalPrice <= max;
        });
    },
    orderByPrice(desc = false) {
        /**
         * Sorts the product list by price.
         *
         * @param {boolean} desc - If true, sorts by descending price (highest to lowest).
         *                         If false, sorts by ascending price (lowest to highest).
         * @returns {Array} - A new array of products sorted by price.
         */
        return [...this.data].sort((a, b) =>
            desc ? b.price - a.price : a.price - b.price
        );
    },
    orderByDiscount() {
        /**
         * Sorts the product list by discount in descending order.
         * Products with the highest discount appear first.
         * Products without discounts (or discount = 0) are shown at the end.
         *
         * @returns {Array} - A new array of products sorted by discount.
         */
        return [...this.data].sort((a, b) => {
            const aDiscount = a.discount || 0;
            const bDiscount = b.discount || 0;
            return bDiscount - aDiscount;
        });
    },


    getUniqueBrands(brands) {
        /**
         * Retrieves the unique brands present in the current list of products.
         *
         * This method uses the `brand_id` of each product in `this.data` to filter
         * the provided list of `brands`, returning only those that are associated
         * with the products. The result is sorted alphabetically by brand name.
         *
         * @param {Array<{id: number, name: string, ...}>} brands - The complete list of available brands.
         * @returns {Array<{id: number, name: string}>} - Array of unique brands present in the products, sorted by name.
         */
        
        // 1. Create a Set of brand_ids present in the current products
        const brandIdsSet = new Set(this.data.map(p => p.brand_id));

        // 2. Filter the list of brands to only include those that exist in the products
        const uniqueBrands = brands.filter(brand => brandIdsSet.has(brand.id));

        // 3. Sort the filtered brands alphabetically by name
        return uniqueBrands.sort((a, b) => a.name.localeCompare(b.name));
    },


    filterByBrand(brandId) {
        /**
         * Filtra los productos por ID de marca
         * @param {number} brandId
         * @returns {Array<Object>}
         */
        if (brandId === 0) return this.data
        return this.data.filter(p => p.brand_id === brandId);
    },

    orderByName() {
        /**
         * Sorts the product list alphabetically by name in ascending order (A-Z).
         *
         * @returns {Array} - A new array of products sorted by name.
         */
        return [...this.data].sort((a, b) => {
            return a.name.localeCompare(b.name);
        });
    },
    filterByName(query) {
        /**
         * Filters the product list based on a search query.
         * The query is split into words, and each word must be included in the product name.
         * The comparison is case-insensitive.
         *
         * @param {string} query - The search string to filter product names.
         * @returns {Array} - A filtered array of products whose names contain all words in the query.
         */
        if (!query) return this.data;

        const words = query.toLowerCase().split(/\s+/); // split by whitespace
        return this.data.filter(p => {
            const name = p.name.toLowerCase();
            return words.every(word => name.includes(word)); // all words must be found
        });
    },
};

window.ProductStore.setData(window.ProductList || []);
delete window.ProductList;  // Elimino la variable global obtenida desde el ssr inicial

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

    const urlBase = `${window.TEMPLATE_URLS.productList.replace('{product_id}', '')}`;
    const url = `${urlBase}/?${params.toString()}`;

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Search failed');
        const data = await response.json();

        // Update product container and product data
        const contProducts = document.getElementById('cont-product-cards');

        // setear nueva lista del fetch
        ProductStore.setData(data.products);
        // actualizar vista
        updateProductListCards(contProducts, data.products, data);
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
 * Updates the pagination control container with page number buttons
 * and sets up an event listener to handle pagination clicks.
 *
 * The container must have two data attributes:
 * - data-total-pages: total number of available pages.
 * - data-page-num: currently active page.
 */
function updateContPagination() {
    const container = document.getElementById('cont-pagination');
    const totalPages = parseInt(container.dataset.totalPages); // Total number of pages
    const pageNum = parseInt(container.dataset.pageNum);       // Current page

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
