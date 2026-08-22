/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../static/js/forms.js" />
/// <reference path="../../../../static/js/utils.js" />
/// <reference path="../../../../static/js/overlay_modal.js" />
/// <reference path="../../../../cart/static/cart/js/components/widget_cart.js" />
/// <reference path="../../../../cart/static/cart/js/logic/cart_store.js" />


/**
 * Handle cart actions: add, subtract, or delete a product from the cart.
 *
 * @param {Object} params
 * @param {number|string} params.productId  - Product ID to operate on
 * @param {"add"|"subtract"|"delete"} params.action - Cart action (default: "add")
 * @param {number} params.quantity - Quantity to add/subtract (default: 1)
 * @param {number} params.stock - Available stock (used to avoid exceeding stock)
 */
async function endpointsCartActions({ 
    productId, 
    action = 'add', 
    quantity = 1, 
    stock = 0,
    showDetail = true
}) {
    // Basic validation — avoid bad or missing product IDs
    const prodId = parseInt(productId);
    if (!productId || Number.isNaN(prodId)) return;

    // Validate allowed actions
    if (!['add', 'subtract', 'delete'].includes(action)) return;

    // Get the current quantity of this product already in the cart
    const cartQuantity = window.CART_STORE.getQuantityById(prodId);

    // When adding items, ensure we don’t exceed available stock
    if (action === 'add') {
        if ((cartQuantity + quantity) > stock) {
            openAlert("No hay suficiente stock", "red", 2000);
            return;
        }
    }

    // Build endpoint URL dynamically
    const url = window.BASE_URLS.cartActions.replace('product_id', prodId);

    // Choose HTTP method depending on the action
    const httpMethod = (action === 'delete') ? 'DELETE' : 'POST';

    // Perform request to backend
    const response = await fetch(url, {
        method: httpMethod,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken'),
        },
        body: JSON.stringify({
            action: action,
            quantity: quantity,
            cart_quantity: cartQuantity
        }),
        // credentials: 'include' // Uncomment if cross-site cookies are needed
    });

    // Parse JSON response from server
    const data = await response.json();

    // Handle server-side errors
    if (!response.ok) {
        openAlert(data.detail, 'red', 1500);
        setTimeout(() => {
            window.location.href = '/'
        }, 1500)
        return;
    }

    // Update local cart store with backend response
    window.CART_STORE.updateCartData(data.cart);

    // Display contextual notification depending on action

    if (showDetail) {
        const colors = {
            add: 'green',
            subtract: 'red',
            delete: 'red'
        };
        openAlert(data.detail, colors[action], 1200);
    }
     
    // Re-render header/cart widget
    renderWidgetCart();

    // If we're on the cart detail page, refresh that view as well
    if (typeof renderTableCartDetail === 'function') {
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

    let pendingChanges = {}

    // Esta función solo se ejecutará cuando el usuario deje de clickear por 500ms
    const debouncedSubmit = debounce(async (form, productId, stock, action, qtyInit) => {
        
        // Dentro del debouncedSubmit:
        const diff = pendingChanges[productId] - qtyInit; 

        let finalAction;
        if (action != 'delete') {
            finalAction = (diff > 0) ? 'add' : 'subtract';

            if (diff === 0) return; // No hubo cambios reales
        } else {
            finalAction = 'delete';
        }
        
        /* for debug
        console.log({
            productId: productId,
            action: finalAction, 
            diff: Math.abs(diff), 
            finalQty: pendingChanges[productId],
            stock: stock
        }); */
        
        await handleGenericFormBase({
            form: form,
            submitCallback: async () => {
                // Enviamos una UNICA petición al servidor con el total acumulado
                await endpointsCartActions({
                    productId: productId,
                    action: finalAction, 
                    quantity:  Math.abs(diff), // Usamos valor absoluto para evitar negativos
                    stock: stock,
                    showDetail: false
                });
                // Una vez enviado con éxito, limpiamos el acumulador para ese producto
                delete pendingChanges[productId];
            }
        });
    }, 500);


    contWidgetCart.addEventListener('submit', (e) => {
        // Only handle form submissions
        if (!e.target.matches('form')) return;
        e.preventDefault();

        // recover values from form
        const form = e.target;
        const productId = form.dataset.index;
        const qtyInit = parseInt(form.dataset.quantity);

        const stock = parseInt(form.dataset.stock);
        const action = e.submitter.dataset.action;

        // --- Lógica de Acumulación ---
        // ?? en lugar de tomar valores falsy, toma valores null o undefined
        let currentQty = pendingChanges[productId] ?? qtyInit;
        // console.log('Current quantity:', currentQty)

        const spans = form.querySelectorAll('.cart-span-items');

        if (currentQty != 0) {
            if (action === 'add') {
                // Regla de Stock: No permitir subir más allá del stock disponible
                if (currentQty < stock) {
                    openAlert("Producto agregado.", "green", 1000);
                    pendingChanges[productId] = currentQty + 1;
                } else {
                    openAlert("Límite de stock alcanzado.", "orange", 1200);
                    return; // Salimos para no disparar el debounce innecesariamente
                }
            } else if (action === 'subtract') {
                // Regla de Mínimo: Si llega a 0, la acción real es eliminar
                if (currentQty > 1) {
                    openAlert("Producto actualizado en el carrito.", "orange", 1000);
                    pendingChanges[productId] = currentQty - 1;
                } else {
                    openAlert("Producto eliminado del carrito.", 'red', 1200);
                    pendingChanges[productId] = 0;
                }
            }

            spans.forEach(s => s.textContent = pendingChanges[productId]);
        }

        if (pendingChanges[productId] === 0 || action === 'delete') {
            openAlert("Producto eliminado del carrito.", 'red', 1200);
            form.classList.add('d-none');
        }

        // Llamamos al debounce pasando el valor final acumulado y la acción final
        debouncedSubmit(form, productId, stock, action, qtyInit);
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

    // primera vez con ssr seteamos datos iniciales para lugar hacer rendering
    try {
        window.CART_STORE = new CartStore(
            JSON.parse(document.getElementById('cart-data').textContent)
        );
    } catch (error) {
        console.error('Error parsing cart data:', error);
        window.CART_STORE = new CartStore({});
    }

    // Render the cart widget on the page once the DOM is fully loaded
    renderWidgetCart();

    // Attach event listeners to open the cart modal or overlay when user interacts
    widgetCartOpenEvent();

    // Delegate event handling inside the cart widget container
    // for buttons like add, subtract, delete on cart items
    widgetCartButtons();
});