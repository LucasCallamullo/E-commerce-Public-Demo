/// <reference path="../../../../../products/static/products/js/components/cards_products.js" />
/// <reference path="../../../../../products/static/products/js/components/carousel_products.js" />
/// <reference path="../../../../../products/static/products/js/logic/cards_products.js" />
/// <reference path="../../../../../products/static/products/js/logic/product_store.js" />


/**
 * Renders a message for when there are no favorite products.
 *
 * @param {HTMLElement} container - The container where the message will be displayed.
 * 
 * This function inserts a friendly Spanish message encouraging the user to browse products,
 * along with a link to the product listing page. It uses `window.TEMPLATE_URLS.productList`
 * to build the link.
 */
function renderEmptyTabFavorites(container) {
    // If no favorites, show a friendly message with a link to browse products
    const url = window.TEMPLATE_URLS.productList;
    const emptyFavs = /*html*/`
        <div class="d-flex-col gap-2 mt-2">
            <h3 class="text-break font-lg">Todavía no hay productos favoritos.</h3>
            <h4 class="text-break font-md">Mira nuestros productos:</h4>
            <a href="${url}" class="w-min text-truncate btn btn-main gap-2 px-2 py-1 bolder font-md">
                <i class="ri-shopping-cart-2-line fw-normal font-lg"></i>Todos nuestros productos
            </a>
        </div>
    `.trim();
    container.innerHTML = emptyFavs;
}


/**
 * Renders the "Favorites" tab carousel.
 *
 * This function is responsible for rendering a favorites carousel inside the
 * provided container. It delegates the actual DOM rendering to a callback
 * (`onRender`) and relies on `createCarouselCards` to handle common carousel
 * initialization logic (events, Swiper setup, etc.).
 *
 * Execution flow:
 * 1. Receives a container element and a list of products (already resolved).
 * 2. Defines an `onRender` callback responsible for:
 *    - Creating the carousel structure
 *    - Rendering product cards
 *    - Handling the empty state
 *    - Initializing Swiper instances
 * 3. Calls `createCarouselCards`, passing the container, products and render callback.
 *
 * Notes:
 * - This function does NOT fetch data.
 * - It does NOT depend directly on global stores.
 * - It is safe to call multiple times with different containers or product lists.
 *
 * @param {HTMLElement} container - DOM element where the favorites carousel will be rendered.
 * @param {Array<Object>} products - List of favorite products to render.
 */
function createTabfavorites(container, products) {
    
    const onRender = (container, products) => {
        // Clear previous content safely (without using innerHTML)
        container.replaceChildren();

        // Temporary holder to reduce reflows
        const fragment = document.createDocumentFragment();

        // Reuse this function since it only requires a name and an index starting from 0
        const { element, swiperWrapper } = renderSwiperCategory('Favoritos', 0);

        // Render and append each product card
        if (products && products.length > 0) {
            products.forEach(product => {
                swiperWrapper.appendChild(renderCards(product, true));
            });
        } else {
            renderEmptyTabFavorites(swiperWrapper);
        }

        // Append the completed carousel to the fragment
        fragment.appendChild(element);

        // Mount everything at once
        container.appendChild(fragment);

        // Initialize Swiper for favorites carousel
        initSwipers(container);
    };

    // carousel_products.js to render favorites and to provide carousel functionality
    createCarouselCards({
        container,
        products,
        onRender
    });
}