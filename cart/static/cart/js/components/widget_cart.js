

/**
 * Stores cart items indexed by product ID for quick access.
 * 
 * @type {Object.<number, Object>}
 * @property {number} key - Product ID.
 * @property {Object} value - Product details (name, price, quantity, etc.).
 * 
 * This global variable is used to store and retrieve products in the cart without
 * repeatedly searching through the cart list. Keys are product IDs, and values
 * contain product information.
 */
window.CART_BY_ID = {};


/**
 * Renders an HTML element representing the "empty cart" state.
 *
 * @returns {HTMLElement} - A DOM element containing the empty cart message and a link to browse products.
 *
 */
function renderTableCartEmpty() {
    const url = encodeURI(window.BASE_URLS.productList);
    const cartHTML = /*html*/`
        <div class="d-flex-col justify-center align-center mt-2 gap-2">
            <h2>Tu carrito esta vacío</h2>
            <div class="w-50 h-150">
                <img src="https://i.pinimg.com/736x/bc/06/d1/bc06d12918b9628f0b886c3f989ba7b2.jpg" 
                class="img-scale-down" alt="Cart Empty" loading="lazy" width="100" height="100">
            </div>
            <a class="btn btn-main w-min text-truncate bolder p-1" href="${url}">
                Ver todos nuestros productos.
            </a>
        </div>
    `.trim();
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = cartHTML;
    return tempDiv.firstElementChild;
}


/**
 * Renders the shopping cart widgets in the page, including both mobile and desktop views.
 * Also updates the total item count badge and total price displays, and handles cart overlay toggling.
 */
function renderWidgetCart() {

    /**
     * Performs post-render updates such as:
     * - Updating the total quantity badge on desktop
     * - Updating total price displays
     * - Automatically opening the cart overlay on non-cart pages if it's closed
     */
    function renderWidgetPost() {
        const header = document.querySelector('header');

        // On Desktop, update the badge showing the total quantity of items in the cart
        const badgeCantTotal = header.querySelector('#badge-cart-button');
        badgeCantTotal.textContent = `${window.CART_DATA.cart_quantity}`;
        
        // Update all elements that display the total price in the cart widget
        const cTotals = header.querySelectorAll('.total__widget__cart');
        const totalPrice = formatNumberWithPoints(window.CART_DATA.cart_price, true);
        cTotals.forEach(t => { t.textContent = `$ ${totalPrice}` });

        // If the user is not on the cart page, check if the cart overlay is closed,
        // and open it automatically on either mobile or desktop.
        const cartView = (window.location.pathname === window.BASE_URLS.cartPageDetail);
        if (!cartView) {
            // Determine device index: Mobile uses index 0, Desktop uses index 1
            const index = IS_MOBILE ? 0 : 1;
            const cartContainer = header.querySelector('.cart-cont-overlay');
            const isOpenCart = cartContainer.getAttribute('data-state') === 'open';

            if (!isOpenCart) {
                const cartButtons = header.querySelectorAll('.cart-button');
                cartButtons[index].click();
            }
        }
    }

    /**
     * Creates a cart item card element from a product object.
     * Escapes data for safety and formats the price with thousands separators.
     * 
     * @param {Object} product - Product data with keys: id, name, image, price, quantity, stock
     * @returns {HTMLElement} - A DOM element representing the cart item
     */
    function renderWidget(product) {
        const prod = deepEscape(product);

        // Use a fallback image if the product image URL is relative or missing
        const imgSrc = prod.image.startsWith('http') ? prod.image : 'default-image.jpg';
        const price = formatNumberWithPoints(prod.price);
        const url = window.BASE_URLS.productDetail.replace('0', prod.id).replace('__SLUG__', prod.slug)
        
        const cardWidget = /*html*/`
            <form class="d-grid cont-cart__card mb-3" data-index="${prod.id}" data-stock="${prod.stock}">

                <a class="cont-img-100-off" href="${url}">
                    <img class="img-scale-down" src="${imgSrc}" alt="${prod.name}" loading="lazy">
                </a>

                <a class="font-sm main-ref bolder text-truncate-multiline mt-1" href="${url}">
                    ${prod.name}
                </a>

                <button class="btn btn-close btn-24 justify-self-end mt-1 me-1" type="submit" data-action="delete">
                    <i class="ri-close-fill font-lg"></i>
                </button>

                <span class="d-flex text-start ms-1 gap-1 bolder">
                    ${prod.quantity}
                    <i class="ri-close-line font-lg"></i>
                    $ ${price}
                </span>
                    
                <div class="cont-numeric-add-less cont-space-between">
                    <button class="btn btn-28 scale-on-touch" type="submit" data-action="substract">
                        <i class="ri-subtract-fill font-lg text-primary"></i>
                    </button>

                    <span class="cart-item-qty">${prod.quantity}</span>
                    
                    <button class="btn btn-28 scale-on-touch" type="submit" data-action="add">
                        <i class="ri-add-fill font-lg text-primary"></i>
                    </button>
                </div>
            </form>
        `.trim();
        const wrapper = document.createElement('div');
        wrapper.innerHTML = cardWidget;
        return wrapper.firstElementChild;
    }

    // Select all containers where the cart widget should be rendered (e.g., mobile and desktop)
    const widget = document.querySelector('.cont-cart__widget');
    const fragment = document.createDocumentFragment();

    if (window.CART_DATA.cart.length > 0) {
        // Render each product as a widget card, append to a document fragment for efficient DOM insertion
        window.CART_DATA.cart.forEach(product => {
            fragment.appendChild(renderWidget(product));

            // Optionally keep track of quantity by product ID for quick lookups (assuming CART_BY_ID exists)
            window.CART_BY_ID[product.id] = product.quantity;
        });
    } else {
        // render empty cart view
        fragment.appendChild(renderTableCartEmpty());
    }

    // Clear existing content and append cloned widget cards to each container (mobile and desktop)
    widget.innerHTML = '';
    widget.appendChild(fragment); // clone the fragment for each container

    // Perform post-render updates (badges, totals, open overlay)
    renderWidgetPost();
}
