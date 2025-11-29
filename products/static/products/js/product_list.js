/// <reference path="../../../../static/js/base.js" />
/// <reference path="./logic/cards_products.js" />
/// <reference path="../js/components/pagination.js" />




/**
 * Initializes the sidebar search form with real-time search functionality.
 * Uses a debounced function to reduce the number of product filter calls while typing.
 *
 * @param {HTMLElement} container - The container where filtered products will be rendered.
 */
function initSearchSidebar(container) {
    const form = document.getElementById('sidebar-search');
    form.lastSearchTerm = '';

    /**
     * Filters products by name and updates the product list in the given container.
     *
     * @param {HTMLElement} container - The container to update with filtered products.
     * @param {string} searchTerm - The user's search query.
     */
    function searchProducts(container, searchTerm) {
        if (searchTerm) {
            const products = ProductStore.filterByName(searchTerm);
            updateProductListCards(container, products);
        }
    }

    // Wrap the search function in a debouncer to delay execution
    const debouncedSearch = debounce(searchProducts, 800);

    form.addEventListener('input', (e) => {
        const searchTerm = e.target.value.trim();
        if (searchTerm !== form.lastSearchTerm) {
            form.lastSearchTerm = searchTerm;
            debouncedSearch(container, searchTerm);
        }
    });
}


/**
 * Dynamically populates the brand container with radio button filters,
 * and sets up event delegation to filter products based on the selected brand.
 *
 * @param {Array} brands - Array of brand objects. Each object should have at least an `id` and a `name` property.
 */
function updateContBrands(contProducts) {
    const container = document.getElementById('cont-brands');
    container.innerHTML = '';
    
    /**
     * Creates a radio input wrapped in a label for a given brand.
     * Crea un input radio envuelto en un label para una marca dada.
     * 
     * @param {Object} brand - Brand object with `id` and `name`
     * @returns {HTMLElement} - The constructed label element
     */
    function createBrandRadio(brand) {
        const b = deepEscape(brand);    // Sanitize brand object to prevent injection

        const labelHTML = /*html*/`
            <label class="d-flex gap-1 radio-brand">
                <input type="radio" name="brand" value="${b.id}">
                ${b.name}
            </label>`;
        const wrapper = document.createElement('div');
        wrapper.innerHTML = labelHTML;
        return wrapper.firstElementChild;
    }

    // Combinar opción "Todos" con las marcas únicas
    const brands = [{ id: 0, name: 'Todos' }, ...ProductStore.getUniqueBrands(window.BRAND_LIST)];
    const fragment = document.createDocumentFragment();
    brands.forEach(brand => { 
        fragment.appendChild(createBrandRadio(brand)); 
    });
    container.appendChild(fragment);

    /**
     * Set up a single event listener using event delegation.
     * This listens for changes on any radio input inside the container.
     */
    if (!container._hasEvent) {
        container.addEventListener('change', (e) => {
            const input = e.target;

            // Ensure the event target is a radio input for brand selection
            if (input.tagName === 'INPUT' && input.type === 'radio' && input.name === 'brand') {
                const brandId = parseInt(input.value); // Get the selected brand ID

                // Filter products using the selected brand ID
                const filtered = ProductStore.filterByBrand(brandId);
                updateProductListCards(contProducts, filtered);

                // Optionally scroll to the updated product section
                scrollToSection(contProducts, 'highlight-main');
            }
        });

        container._hasEvent = true;
    }
}


/**
 * Updates the price filter UI and product list based on the selected price range.
 * 
 * @param {HTMLElement} contProducts - The container element where product cards are rendered.
 */
function updateContPrices(contProducts) {
    const sidebarCont = document.getElementById('sidebar-list');
    const minRange = sidebarCont.querySelector('#min-range');
    const maxRange = sidebarCont.querySelector('#max-range');
    const spanMin = sidebarCont.querySelector('#min-val');
    const spanMax = sidebarCont.querySelector('#max-val');
    const track = sidebarCont.querySelector('.slider-track');

    // Limpiar event listeners anteriores si existen
    if (minRange._updateSliderHandler) {
        minRange.removeEventListener('input', minRange._updateSliderHandler);
        maxRange.removeEventListener('input', minRange._updateSliderHandler);
    }

    // Get current min and max prices from product store (considering discounts)
    const { min: minPrice, max: maxPrice } = ProductStore.getPriceRange();

    console.log(`Precio mayor: ${minPrice} - Precio menor: ${maxPrice}`)

    // Set the actual limits for the range sliders
    minRange.min = minPrice;
    minRange.max = maxPrice;
    minRange.value = minPrice;

    maxRange.min = minPrice;
    maxRange.max = maxPrice;
    maxRange.value = maxPrice;

    // Set step size for slider increments (fixed to 100 in this example)
    const step = 100;
    minRange.step = step;
    maxRange.step = step;

    // Create a debounced function to filter products and update the UI
    const debouncedFilter = debounce((min, max) => {
        const filteredProducts = ProductStore.filterByPrice(min, max);
        updateProductListCards(contProducts, filteredProducts);

        // hacer movimiento visual al nuevo grupo de tarjetas
        // scrollToSection(contProducts, 'highlight-main');
    }, 800);

    const visualTrack = (min, max) => {
        // Update the visible min and max values text
        spanMin.textContent = min;
        spanMax.textContent = max;

        // Calculate slider percentages for the gradient background
        const range = maxPrice - minPrice;

        // evitar division por cero
        let percentMin = 0;
        let percentMax = 100;
        if (range > 0) {
            percentMin = ((min - minPrice) / range) * 100;
            percentMax = ((max - minPrice) / range) * 100;
        }

        // Set slider track background
        track.style.background = `linear-gradient(to right, 
            var(--bg-primary) ${percentMin}%,
            var(--main-color) ${percentMin}%,
            var(--main-color) ${percentMax}%,
            var(--bg-primary) ${percentMax}%)`;
    }

    // Function to handle slider input changes
    const updateSlider = (e = null) => {
        let min = parseInt(minRange.value);
        let max = parseInt(maxRange.value);

        // Prevent sliders from crossing over
        if (min > max) {
            if (e && e.target === minRange) {
                min = max;
                minRange.value = max;
            } else if (e) {
                max = min;
                maxRange.value = min;
            }
        }
        visualTrack(min, max);
        
        if (e) debouncedFilter(min, max);
    };

    // Guardar referencia a la función para poder eliminarla después
    minRange._updateSliderHandler = updateSlider;

    // Add event listeners
    minRange.addEventListener('input', updateSlider);
    maxRange.addEventListener('input', updateSlider);

    // Actualizar visualización inicial
    visualTrack(minPrice, maxPrice);
}


function initFormSort(contProducts) {
    const select = document.getElementById('select-to-sort');
    
    const sortMethods = {
        priceAsc: () => ProductStore.orderByPrice(false),
        priceDesc: () => ProductStore.orderByPrice(true),
        getList: () => ProductStore.getData(),
        name: () => ProductStore.orderByName(),
        discount: () => ProductStore.orderByDiscount(),
    };

    select.addEventListener('change', (e) => {
        const value = e.target.value;
        const sorted = (sortMethods[value] || sortMethods['getList'])();
        ProductStore.setData(sorted);
        updateProductListCards(contProducts, sorted);
    });
}



/**
 * Initializes the product listing page once the DOM is fully loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
    // Container element for product cards
    const container = document.getElementById('cont-product-cards');

    // Update the brand filters UI based on available data
    updateContBrands(container);

    // Update the price filter sliders and values
    updateContPrices(container);

    // Render the full product list initially
    updateProductListCards(container, ProductStore.getData());

    // Initialize the sidebar search bar with real-time search and debounce
    initSearchSidebar(container);

    initFormSort(container);

    // Setup pagination controls UI and logic
    updateContPagination();

    // Setup the history popstate event listener to handle browser back/forward navigation
    historyPopState();

    // If the URL has query parameters, parse and fetch the product list accordingly
    const params = new URLSearchParams(window.location.search);
    if (params.toString()) {
        const dict = {};
        for (const [key, value] of params.entries()) {
            dict[key] = value;
        }
        fetchProductList(dict);
    }
});
