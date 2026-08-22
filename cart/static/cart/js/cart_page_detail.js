/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../favorites/static/favorites/js/add_favorites.js" />
/// <reference path="../../../../cart/static/cart/js/components/table_cart_detail.js" />


/**
 * Attaches a submit event listener to the given cart table container.
 * 
 * This function listens for form submissions within the `tableCartView` element and handles different
 * types of cart actions based on the class of the submitted form:
 * 
 * - `.form-to-like`   → Adds/removes product from favorites.
 * - `.form-to-add`    → Increases product quantity in cart.
 * - `.form-to-less`   → Decreases product quantity in cart.
 * - `.form-to-delete` → Removes product entirely from cart.
 * 
 * It delegates the handling to `handleGenericFormBase` with appropriate callbacks, and also uses 
 * `e.submitter` to access the actual button that triggered the submit.
 *
 * @param {HTMLElement} containerMain - The DOM element representing the container for cart forms.
 */
function eventsTableCartDetail(containerMain) {

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


    const tableCartDetail = containerMain.querySelector('#table-cart-detail');
    tableCartDetail.addEventListener('submit', async (e) => {

        // Only handle form submissions
        if (!e.target.matches('form')) return;

        e.preventDefault();
        const form = e.target;
        const btn = e.submitter;    // The button that triggered the form submission
        if (!btn) return;
        const action = btn.dataset.action;    // add, substract, delete, like
        const productId = form.dataset.index;

        /* ---- Handle product favorite (like) form ---- */
        if (action === 'like') {
            await handleGenericFormBase({
                form: form,
                submitCallback: async () => formFavoritesEvents(productId, btn),
                flag_anim: false, // Disable spinner animation
            });
            return;
        }

        /* ---- Handle cart actions (add, subtract, delete) ---- */
        // --- Lógica de Acumulación ---

        // ?? en lugar de tomar valores falsy, toma valores null o undefined
        const qtyInit = parseInt(form.dataset.quantity);
        const stock = parseInt(form.dataset.stock);
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

        /* ---- Handle cart actions (add, subtract, delete) ---- 
        const stock = parseInt(form.dataset.stock) || 0;
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
        }); */
    });
}


/**
 * Initializes event listeners once the DOM is fully loaded.
 * 
 * - Attaches cart-related form functionality to the cart view container.
 * - Handles placeholders for future features such as coupon application and cart update.
 */
document.addEventListener('DOMContentLoaded', () => {
    
    const containerMain = document.getElementById('cont-main-cart-detail');
    
    // render inicial table with data cart
    renderTableCartDetail(containerMain);

    // Attach event delegation logic to handle add/subtract/delete/favorite actions in cart
    eventsTableCartDetail(containerMain);

    /* Form Cupon hacer algun día */
    const formCupon = containerMain.querySelector('#form-coupon');
    formCupon.addEventListener('submit', (e) => {
        e.preventDefault();
        openAlert('trabajando en esto todavía.', 'orange', 1500);
    });

    /* Form Update Carrito hacer algun día */
    const formUpdateCart = containerMain.querySelector('#form-update-cart');
    formUpdateCart.addEventListener('submit', (e) => {
        e.preventDefault();
        openAlert('trabajando en esto todavía.', 'orange', 1500);
    });
});