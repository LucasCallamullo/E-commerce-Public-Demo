
function renderTableModal(containerMain) {
    /**
     * Render a single cart row for the cart table.
     * 
     * @param {Object} product - Product data object from CART_DATA.
     * @param {number} index - Position of the product in the list (0-based).
     * @returns {HTMLElement} - A DOM element representing the product row.
     */
    function renderTableCart(product, index) {
        const prod = deepEscape(product); // Ensure values are safe for HTML

        // Use a fallback image if missing or relative
        const imgSrc = prod.image.startsWith('http') ? prod.image : 'default-image.jpg';
        const price = formatNumberWithPoints(prod.price);
        const subTotal = formatNumberWithPoints((prod.price * prod.quantity));

        // Build product detail URL
        const url = window.BASE_URLS.productDetail
            .replace('0', prod.id)
            .replace('__SLUG__', prod.slug);

        const cardWidget = /*html*/`
            <div class="cart-row ${(index == 0) ? 'border-top-tablets' : ''}">
                <div class="image cont-img-100-off">
                    <img class="img-scale-down" src="${imgSrc}" alt="${prod.name}">
                </div>

                <a class="name text-start bolder font-sm main-ref" href="${url}">
                    ${prod.name}
                </a>

                <span class="price font-md bolder">
                    $ ${price}
                    <i class="ri-close-line font-md bolder"></i>
                </span>
                
                <span class="quantity font-md bolder">
                    ${prod.quantity}
                    <i class="ri-equal-line"></i>
                </span>

                
                <span class="subtotal bolder">
                    <b class="d-mobile-flex"> SubTotal: </b>
                    $ ${subTotal}
                </span>
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
                </div>
            `.trim();
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = headerHTML;
        return tempDiv.firstElementChild;
    }

    // CART_DATA contains the current cart state, populated by SSR or via AJAX.
    const fragment = document.createDocumentFragment();

    // Render each cart product. Add header row before the first product.
    window.CART_DATA.cart.forEach((product, index) => {
        if (index == 0) fragment.appendChild(renderHeaderTable());
        fragment.appendChild(renderTableCart(product, index));
    });

    // Clear current table and insert the updated cart rows
    const tableModal = containerMain.querySelector('#modal-table-order');
    tableModal.innerHTML = '';
    tableModal.appendChild(fragment);

    // Update all total price displays in the container
    const contTotals = containerMain.querySelectorAll('.modal-table-total');
    const totalPrice = formatNumberWithPoints(window.CART_DATA.cart_price, true);
    contTotals.forEach(t => { t.textContent = `$ ${totalPrice}` });
}