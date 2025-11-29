/// <reference path="../../../../../static/js/base.js" />
/// <reference path="../../../../../static/js/utils.js" />



/**
 * Renders a label indicating the stock status of a product.
 *
 * @param {Object} prod - The product object.
 * @param {boolean} prod.available - Whether the product is available for sale.
 * @param {number} prod.stock - The current stock quantity.
 * @returns {string} HTML string with the appropriate stock label.
 */
function renderStockLabel(prod) {
    if (!prod.available || prod.stock == 0) {
        return /*html*/`<p class="text-start text-truncate bold-red">No disponible</p>`;
    } else if (prod.stock <= 3) {
        return /*html*/`<p class="text-start text-truncate bold-orange">Stock Bajo</p>`;
    }
    return /*html*/`<p class="text-start text-truncate bold-green">Disponible</p>`;
}


/**
 * Renders a heart icon button to represent whether the product is in the user's favorites.
 *
 * @param {Object} prod - The product object.
 * @param {boolean} prod.is_favorited - Indicates if the product is favorited by the user.
 * @returns {string} HTML string with a heart icon button (filled or outlined).
 */
function renderFavoritesLabel(prod) {
    const heartClass = prod.is_favorited ? ICONS.heart : ICONS.heartEmpty;
    return /*html*/`
        <button class="btn btn-36 btn-like ${prod.is_favorited ? 'liked' : ''}" type="submit">
            <i class="${heartClass} font-xl"></i>
        </button>`;
}


/**
 * Renders the HTML for a product's pricing label, showing discount information if applicable.
 * 
 * @param {Object} prod - The product object.
 * @param {number} prod.price - Original product price.
 * @param {number} prod.discount - Discount percentage (0–100).
 * @returns {string} HTML string representing the price section of the product card.
 */
function renderDiscountLabel(prod) {
    const price = formatNumberWithPoints(prod.price);

    // If there is no discount, show only the normal price
    if (prod.discount <= 0) {
        return /*html*/`<p class="text-start bolder font-lg grid-col-all"> $ ${price}</p>`;
    }

    const price_discount = formatNumberWithPoints(prod.price - (prod.price * prod.discount / 100));
    return /*html*/`
        <b class="text-line-through text-secondary font-md">$${price}</b>
        <b class="justify-self-end text-white product-card__offer-tag text-truncate font-xs">${prod.discount}% OFF</b>
        <b class="bolder font-lg grid-col-all">$ ${price_discount}</b>`;
}


function renderCards(product, isSwiper=false) {
    // Sanitize product data to prevent XSS or unwanted HTML injection
    const prod = deepEscape(product);

    // Build the detail URL by replacing placeholders with actual product ID and slug
    const urlDetail = encodeURI(
        window.TEMPLATE_URLS.productDetail
            .replace('0', prod.id)
            .replace('__SLUG__', prod.slug)
    );

    // Use a fallback image if the product image is not an absolute URL
    const imgSrc = prod.main_image.startsWith('http') ? prod.main_image : 'default-image.jpg';

    // Construct the HTML string for a single product card
    const cardHTML = /*html*/`
        <article class="product__card w-100 relative ${(isSwiper) ? 'swiper-slide' : ''}">
            <button class="btn corner-box" data-id="${prod.id}">
                <i class="ri-focus-mode font-xl"></i>
            </button>
            
            <div class="d-grid h-100 w-100 product-card__info">
                <a href="${urlDetail}" class="cont-img-100">
                    <img class="img-scale-down" src="${imgSrc}" alt="${prod.name}"
                    loading="lazy" width="100" height="100">
                </a>

                <a class="px-2 text-start text-truncate-multiline font-md bolder" href="${urlDetail}">
                    ${prod.name}
                </a>

                <div class="d-grid px-2 product-card__grid-2 gap-2 align-center font-sm">
                    ${renderStockLabel(prod)} 
                    <form class="justify-self-end form-btn__like" data-index="${prod.id}">
                        ${renderFavoritesLabel(prod)} 
                    </form>
                    ${renderDiscountLabel(prod)} 
                </div>
            </div>

            <form class="d-flex justify-center product-card__extender-btn" 
            data-index="${prod.id}" data-stock="${prod.stock}">
                <button class="btn btn-main gap-1 btn-32 w-75 btn-add-product-pc font-md bolder" type="submit">
                    Agregar<i class="ri-shopping-basket-2-fill"></i>
                </button>
            </form>
        </article>
    `;

    /**
     * Converts the HTML string to DOM elements:
     * - A temporary <div> wrapper is created and populated with the cardHTML
     * - The <article> element is extracted as the firstElementChild
     * - It is then appended to the DocumentFragment
     * - The temporary <div> is discarded automatically by the garbage collector
     */
    const wrapper = document.createElement('div');
    wrapper.innerHTML = cardHTML;
    return wrapper.firstElementChild;
}


/**
 * Renders a list of product cards into a given container element.
 *
 * @param {HTMLElement} container - The DOM element where product cards will be rendered.
 * @param {Array<Object>} products - List of product objects to render.
 */
function renderingListCard(container, products) {
    container.innerHTML = '';

    // Create an in-memory lightweight container for DOM nodes
    // This reduces layout thrashing by batching DOM insertions
    const fragment = document.createDocumentFragment();

    products.forEach(prod => {
        fragment.appendChild(renderCards(prod)); 
    });

    // Append all product cards to the DOM in a single operation
    container.appendChild(fragment);
}


/**
 * Renders a default card message when the container (e.g., order list, cart, etc.) is empty.
 * This provides feedback to the user and offers a shortcut to view all available products.
 *
 * @param {HTMLElement} container - The DOM element where the empty message should be rendered.
 */
function renderingEmptyListCard(contProducts) {
    contProducts.innerHTML = '';
    const cardHtml = /*html*/`
        <h1 class="grid-col-all mt-1 text-break font-lg">Ningún Producto cumple con tus filtros.</h1>
        <h2 class="grid-col-all text-break font-md">Volve a mirar todos nuestros productos:</h2>
        <div class="grid-col-all justify-self-center">
            <button class="w-min text-truncate btn btn-main gap-2 px-2 py-1 bolder font-md" id="get-all-products">
                <i class="ri-shopping-cart-2-line font-lg"></i>
                Todos los Productos
            </button>
        </div>
    `;
    contProducts.insertAdjacentHTML('beforeend', cardHtml);
    const btn = contProducts.querySelector('#get-all-products');

    if (btn && !btn._hasInitEvents) {
        btn.addEventListener('click', () => {
            // Call function to fetch all available products (category 0 = all, subcategory 0 = all)
            // fetchProductList({ available: 1, category: 0, subcategory: 0 });
            if (window.ProductStore && typeof ProductStore.getData === 'function') {
                updateProductListCards(contProducts, ProductStore.getData());
            }
        });
        // Mark the button as initialized
        btn._hasInitEvents = true;
    }
}


function updateProductListCards(container, products, data = null) {

    if (!container) {
        console.error('container no encontrado');
        return;
    }

    if (products.length > 0) {
        renderingListCard(container, products);
    } else {
        renderingEmptyListCard(container);
    }

    // set events one time on static container
    if (!container._hasInitEvents) {
        productCardFormsEvents(container);
        productCardModalEvent(container);
        container._hasInitEvents = true;
    }
}

