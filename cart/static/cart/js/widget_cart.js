/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../static/js/forms.js" />
/// <reference path="../../../../static/js/utils.js" />
/// <reference path="../../../../static/js/overlay-modal.js" />
/// <reference path="../../../../cart/static/cart/js/components/widget_cart.js" />


async function endpointsCartActions({ productId, action = 'add', quantity = 1, stock = 0 }) {
    
    // Stupids Check
    const prodId = parseInt(productId);
    if (!productId || Number.isNaN(prodId)) return;
    if (!['add', 'substract', 'delete'].includes(action)) return;

    // CART_DATA es variable global, cantidad actual en carrito (from base.html)
    const cartQty = parseInt(window.CART_BY_ID[prodId]) || 0;

    if (action == 'add') {
        // Verificar stock en frontend (opcional)
        if ((cartQty + quantity) > stock) {
            openAlert("No hay suficiente stock", "red", 2000);
            return;
        }
    }

    const url = window.BASE_URLS.cartActions.replace('{product_id}', prodId);
    // default 'POST' for action: add & substract
    const httpMethod = (action === 'delete') ? 'DELETE' : 'POST';

    // Se realiza el fetch según el endpoint de la acción
    const response = await fetch(url, {
        method: httpMethod,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            action: action,
            quantity: quantity,
            cart_quantity: cartQty
        }),
        // credentials: 'include'  // Descomenta si necesitas enviar cookies/CORS
    });

    // recibimos json de respuesta
    const data = await response.json();
    if (!response.ok) {
        openAlert(data.detail, 'red', 1500);
        return;
    }
    window.CART_DATA = data.cart;

    // Handle interactive alert // remember, all responses have this data
    colors = {
        'add': 'green',
        'substract': 'red',
        'delete': 'red'
    }
    openAlert(data.detail, colors[action], 1200);

    // renderizar el widget principal en cada vista
    renderWidgetCart();

    // if you are in the cart-view-page update the view
    // typeof == only use the function if is define in my current context
    if (typeof renderTableCartDetail === 'function') {
        // para renderizar la tabla en la page detail
        renderTableCartDetail();
    }
}


/**
 * Sets up delegated event listeners on cart container elements.
 * 
 * This function attaches a single 'submit' event listener to each container,
 * instead of binding individual listeners to each button or form.
 * 
 * It uses event delegation: the listener checks if the submitted form matches 
 * one of the expected form types (add, subtract, delete). This approach ensures 
 * that new forms dynamically added via innerHTML replacement will still be handled 
 * without needing to re-assign individual listeners.
 * 
 */
function widgetCartButtons() {
    const contWidgetCart = document.querySelector('.cont-cart__widget ');
    contWidgetCart.addEventListener('submit', async (e) => {
        // Only handle form submissions
        if (!e.target.matches('form')) return;
        e.preventDefault();

        // recover values from form
        const form = e.target;
        const productId = form.dataset.index;
        const stock = parseInt(form.dataset.stock);

        // recover values from btn
        const btn = e.submitter;
        const action = btn.dataset.action;

        await handleGenericFormBase({
            form: form,
            submitCallback: async () => {
                await endpointsCartActions({
                    productId: productId,
                    action: action,
                    quantity: 1,
                    stock: stock
                });
            }
        });
    });
}


/**
 * Handles the opening behavior of the shopping cart widget.
 * 
 * - Blocks the cart from opening on specific pages (order and payment).
 * - Shows an alert instead if the user tries to open it on those pages.
 * - On allowed pages, connects each cart button with its corresponding
 *   cart container, overlay, and close button using `setupToggleableElement`.
 */
function widgetCartOpenEvent() {
    // Define the pages where the cart widget should NOT be activated
    const blockedPages = [
        window.BASE_URLS.resumeOrder       // Blocked: order page
    ];

    const header = document.querySelector('header');    // header from page

    const buttons = header.querySelectorAll('.cart-button');         // Cart buttons
    const container = header.querySelector('.cart-cont-overlay');   // Cart container overlays
    const overlay = header.querySelector('.cart-overlay');        // Cart content overlays
    const btnClose = container.querySelector('.close-widget-cart');  // Cart close buttons

    // For each cart button, associate it with its corresponding elements
    buttons.forEach((btn) => {

        // Setup toggle behavior for this cart widget
        setupToggleableElement({
            toggleButton: btn,
            closeButton: btnClose,
            element: container,
            overlay: overlay,
            onOpenCallback: () => {
                // debido al stack entre z-index se agrega un nuevo valor al abrir el cart para que este 
                // por encima de todos los modales
                if (IS_MOBILE) {
                    header.classList.add('cart-open');
                }
            },
            onCloseCallback: () => {
                if (IS_MOBILE) {
                    header.classList.remove('cart-open');
                }
            },
            shouldOpen: (e) => {
                const currentPath = window.location.pathname;

                // If the current page is blocked, disable cart functionality
                if (blockedPages.includes(currentPath)) {
                    // Add a click event listener to each cart button to show an alert
                    openAlert('No puedes usar el Carrito durante el pedido y/o pago.', 'green', 2000);
                    // Stop the function to prevent further setup
                    return false;
                }
                return true;
            }
        });
    });
}


document.addEventListener('DOMContentLoaded', () => {
    // Render the cart widget on the page once the DOM is fully loaded
    renderWidgetCart();

    // Attach event listeners to open the cart modal or overlay when user interacts
    widgetCartOpenEvent();

    // Delegate event handling inside the cart widget container
    // for buttons like add, subtract, delete on cart items
    widgetCartButtons();
});