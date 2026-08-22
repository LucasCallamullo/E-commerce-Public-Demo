

/**
 * CartStore class
 * 
 * @param {Object} cartData - El objeto JSON con la estructura del carrito
 * @param {Array<Object>} cartData.items - Lista de items en el carrito
 * @param {number} cartData.total_price - Total sin descuentos
 * @param {number} cartData.total_price_discount - Total con descuentos aplicados
 * @param {number} cartData.total_quantity - Total de items en el carrito
 * 
 * Cada item dentro de items:
 * @param {number} item.id - ID del producto
 * @param {string} item.name - Nombre del producto
 * @param {string} item.slug - Slug del producto
 * @param {number} item.price - Precio unitario sin descuento
 * @param {string} item.image - URL de la imagen
 * @param {number} item.quantity - Cantidad en el carrito
 * @param {number} item.stock - Stock disponible
 * @param {number} item.discount - Porcentaje de descuento (0-100)
 * @param {number} [item.price_discount] - Precio unitario con descuento (calculado)
 */
class CartStore {
    /**
     * Creates a new cart store instance.
     *
     * @param {Object} cartData - Cart JSON coming from SSR or API.
     * @param {Array} cartData.items
     * @param {number} cartData.total_price
     * @param {number} cartData.total_price_discount
     * @param {number} cartData.total_quantity
     */
    constructor(cartData = {}) {
        this.items = cartData?.items || [];
        this.totalPrice = cartData?.total_price || 0;
        this.totalPriceDiscount = cartData?.total_price_discount || 0;
        this.totalQuantity = cartData?.total_quantity || 0;

        // Add price_discount to each item
        this.items.forEach(item => {
            item.price_discount = this.calculateItemDiscount(item);
        });
    }

    /**
     * Returns a cart item by product id.
     *
     * @param {number} productId
     * @returns {Object|null} Item if found, otherwise null.
     */
    getItemById(productId) {
        return this.items.find(item => item.id === productId) || null;
    }

    /**
     * Returns the quantity for a given product id.
     *
     * @param {number} productId
     * @returns {number} Quantity, or 0 if not found.
     */
    getQuantityById(productId) {
        const item = this.getItemById(productId);
        return item ? item.quantity : 0;
    }

    /**
     * Calculates the discounted price for a single item.
     *
     * @param {Object} item
     * @param {number} item.price
     * @param {number} [item.discount] - Discount percentage (0–100)
     * @returns {number} Final price with discount applied.
     */
    calculateItemDiscount(item) {
        const discount = item.discount ?? 0;

        const base = discount > 0
            ? item.price * (1 - discount / 100)
            : item.price;

        // "+" converts to number after toFixed returns a string
        return +base.toFixed(2);
    }

    /**
     * Returns how much the user saves in total.
     *
     * @returns {number}
     */
    getTotalDiscount() {
        return this.totalPrice - this.totalPriceDiscount;
    }

    /**
     * Returns a safe copy of the cart,
     * useful for rendering or sending back to the API.
     *
     * @returns {{
     *   items: Array,
     *   total_price: number,
     *   total_price_discount: number,
     *   total_quantity: number
     * }}
     */
    getCartData() {
        return {
            items: [...this.items],
            total_price: this.totalPrice,
            total_price_discount: this.totalPriceDiscount,
            total_quantity: this.totalQuantity
        };
    }

    /**
     * Updates internal cart state with new data
     * (for example after an API response),
     * and recalculates all item discounted prices.
     *
     * @param {Object} cartData
     */
    updateCartData(cartData = {}) {
        this.items = cartData.items || [];
        this.totalPrice = cartData.total_price || 0;
        this.totalPriceDiscount = cartData.total_price_discount || 0;
        this.totalQuantity = cartData.total_quantity || 0;

        this.items.forEach(item => {
            item.price_discount = this.calculateItemDiscount(item);
        });
    }
}