

function renderTableCartDetail(containerMain = null) {

    /**
     * Render a single cart row for the cart table.
     * 
     * @param {Object} product - Product data object from CART_DATA.
     * @param {number} index - Position of the product in the list (0-based).
     * @param {Set<number>} favoriteProducts - Set of product IDs marked as favorites.
     * @returns {HTMLElement} - A DOM element representing the product row.
     */
    function renderTableCart(product, index, favoriteProducts) {
        const prod = deepEscape(product); // Ensure values are safe for HTML

        // Use a fallback image if missing or relative
        const imgSrc = prod.image.startsWith('http') ? prod.image : 'default-image.jpg';
        const price = formatNumberWithPoints(prod.price);
        const subTotal = formatNumberWithPoints((prod.price * prod.quantity));

        // Build product detail URL
        const url = window.BASE_URLS.productDetail
            .replace('0', prod.id)
            .replace('__SLUG__', prod.slug);

        // Check if the product is in favorites
        const isLiked = favoriteProducts.has(prod.id);

        const cardWidget = /*html*/`
            <div class="cart-row ${(index == 0) ? 'border-top-tablets' : ''}">

                <div class="image cont-img-100-off">
                    <img class="img-scale-down" src="${imgSrc}" alt="${prod.name}" 
                        loading="lazy" width="100" height="100">
                </div>

                <a class="name justify-start text-start bolder font-sm main-ref" href="${url}">
                    ${prod.name}
                </a>

                <div class="price font-md bolder">
                    $ ${price}<i class="ri-close-line"></i>
                    ${prod.quantity}<i class="ri-equal-line"></i>
                </div>

                <div class="quantity">
                    <form class="cont-numeric-cart-detail cont-space-between justify-self-end" 
                    data-index="${prod.id}" data-stock="${prod.stock}">
                        <button class="btn btn-28 scale-on-touch cart-view-minus" type="submit" 
                        data-action="substract">
                            <i class="ri-subtract-fill font-lg text-primary"></i>
                        </button>

                        <span class="cart-item-qty cart-view-input-qty" readonly>${prod.quantity}</span>
                        
                        <button class="btn btn-28 scale-on-touch cart-view-plus" type="submit"
                        data-action="add">
                            <i class="ri-add-fill font-lg text-primary"></i>
                        </button>
                    </form>
                </div>

                <div class="subtotal bolder">
                    <span class="d-tablet-flex"> SubTotal: </span>$ ${subTotal}
                </div>

                <form class="actions gap-1" data-index="${prod.id}">
                    <button type="submit" class="btn btn-32 btn-like ${(isLiked) ? 'liked' : ''}"
                    data-action="like">
                        <i class="ri-heart-fill font-xl"></i>
                    </button>
                
                    <button type="submit" class="btn btn-32 btn-like" data-action="delete">
                        <i class="ri-close-fill font-xl"></i>
                    </button>
                </form>
            </div>
        `.trim();

        const wrapper = document.createElement('div');
        wrapper.innerHTML = cardWidget;
        return wrapper.firstElementChild;
    }


    /**
     * Render the table header for desktop view.
     * 
     * @returns {HTMLElement} - DOM element representing the table header row.
     */
    function renderHeaderTable() {
        const headerHTML = /*html*/`
                <div class="d-desktop-grid cart-row row-header border-bot-prim">
                    <span class="images"></span>
                    <strong class="name">Producto</strong>
                    <strong class="price">Precio</strong>
                    <strong class="quantity">Cantidad</strong>
                    <strong class="subtotal">SubTotal</strong>
                    <span class="actions"></span>
                </div>
            `.trim();
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = headerHTML;
        return tempDiv.firstElementChild;
    }

    // Create a set with the user's favorite product IDs
    const favoriteProducts = new Set(window.PRODUCTS_FAVORITES);

    // CART_DATA contains the current cart state, populated by SSR or via AJAX.
    const fragment = document.createDocumentFragment();

    if (window.CART_DATA.cart.length > 0) {
        // Render each cart product. Add header row before the first product.
        window.CART_DATA.cart.forEach((product, index) => {
            if (index == 0) fragment.appendChild(renderHeaderTable());
            fragment.appendChild(renderTableCart(product, index, favoriteProducts));
        });
    } else {
        // render empty cart view
        if (typeof renderTableCartEmpty === 'function') fragment.appendChild(renderTableCartEmpty());
    }

    // Determine where to render: use provided container or fallback to default ID
    let contMain = containerMain;
    if (!contMain) {
        contMain = document.getElementById('cont-main-cart-detail');
    }

    // Clear current table and insert the updated cart rows
    const tableCart = contMain.querySelector('#table-cart-detail');
    tableCart.innerHTML = '';
    tableCart.appendChild(fragment);

    // Update all total price displays in the container
    const contTotals = contMain.querySelectorAll('.total-cart-detail');
    const totalPrice = formatNumberWithPoints(window.CART_DATA.cart_price, true);
    contTotals.forEach(t => { t.textContent = `$ ${totalPrice}` });
}
