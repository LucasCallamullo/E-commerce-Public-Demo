

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
 * Creates and renders the "Favorites" tab carousel.
 *
 * @param {HTMLElement} container - The container where the favorites carousel will be rendered.
 * @param {Array<Object>} products - List of product objects to display as favorites.
 *
 * This function:
 *  - Clears the container.
 *  - Stores product data using `ProductStore.setData`.
 *  - Creates a swiper carousel for the "Favoritos" category.
 *  - If there are products, it appends each as a card inside the carousel and initializes Swiper.
 *  - If there are no products, it calls `renderEmptyTabFavorites` to show the empty state message.
 */
function createTabfavorites(container, products) {
    container.innerHTML = '';

    // All logic below depends on carousel_cards and related functions from that module
    ProductStore.setData(products);
    const fragment = document.createDocumentFragment(); // Temporary holder to reduce reflows

    // Reuse this function since it only requires a name and an index starting from 0
    const { element, swiperWrapper } = renderSwiperCategory('Favoritos', 0);

    // Render and append each product card
    if (products && products.length > 0) {
        products.forEach(product => {
            swiperWrapper.appendChild(renderCards(product, true));
        });
        initSwipers(container);
    } else {
        renderEmptyTabFavorites(swiperWrapper);
    }

    // Append the completed carousel to the fragment
    fragment.appendChild(element);
    container.appendChild(fragment);
}