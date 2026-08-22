// Diccionario de ID: boolean (true = favorito, false = no favorito)
let pendingFavorites = {};

// 1. CREAR LA FUNCIÓN UNA SOLA VEZ (AFUERA)
const debouncedFavoriteSubmit = debounce(async (productId, btn, form, finalState) => {

    // Verificamos si el estado final es distinto al que ya tiene window.FAVORITES_LIST
    // para evitar peticiones innecesarias si el usuario clickeó 2 veces (volvió al inicio)
    const isCurrentlyFavorited = window.FAVORITES_LIST?.includes(parseInt(productId));
    
    // Si después de tantos clicks volvió al estado original, no molestamos al servidor
    if (finalState === isCurrentlyFavorited) {
        delete pendingFavorites[productId];
        return; 
    }

    await handleGenericFormBase({
        form,
        submitCallback: async () => {
            await formFavoritesEvents(productId, btn);
            delete pendingFavorites[productId];
        },
        flag_anim: false,
    });
}, 1000);


function debounce_on_favorites(productId, btn, form) {

    // --- LÓGICA OPTIMISTA (UI INSTANTÁNEA) ---
    // 1. Determinar el estado actual basado en la clase o en pendingFavorites
    const currentState = pendingFavorites[productId] ?? btn.classList.contains("liked");
    // console.log("=====================================================================");
    // console.log('CURRENT STATE: ', currentState);
    
    const newState = !currentState;
    // console.log('NEW STATE: ', newState);

    // 2. Guardar en memoria el deseo del usuario
    pendingFavorites[productId] = newState;

    // 3. Cambiar visualmente el botón YA MISMO
    const icon = btn.querySelector('i');
    if (newState) {
        btn.classList.add("liked");
        icon.classList.replace(ICONS.heartEmpty, ICONS.heart);
    } else {
        btn.classList.remove("liked");
        icon.classList.replace(ICONS.heart, ICONS.heartEmpty);
    }

    // 4. Mandar al servidor con retraso
    debouncedFavoriteSubmit(productId, btn, form, newState);
}




/**
 * Lógica para añadir o quitar favoritos de un producto.
 * 
 * @param {string} productId - ID del producto.
 * @param {HTMLButtonElement} btn - Botón de submit que activó el formulario.
 */
async function formFavoritesEvents(productId, btn) {

    // Si no está logueado, muestra alerta y detiene el flujo con un error.
    if (!AUTH_STATUS) {
        openAlert('Debe logearse para guardar en Favoritos.', 'red', 2500);
        return;
    }

    try {
        const url = window.TEMPLATE_URLS.favorites.replace('{product_id}', productId);
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'), // Django CSRF
            },
            body: JSON.stringify({ product_id: productId }),
        });

        const data = await response.json();

        if (!response.ok) {
            // Si la API devuelve error de lógica
            openAlert('Error al guardar favorito.' || data.detail, 'red', 1500);
            return;
        }

        const icon = btn.querySelector('i');
        if (data.is_favorite) {
            openAlert('Producto agregado como Favorito!', 'green', 1500);
            btn.classList.add("liked");
            icon.classList.replace(ICONS.heartEmpty, ICONS.heart);
        } else {
            openAlert('Producto eliminado como Favorito.', 'red', 1500);
            btn.classList.remove("liked");
            icon.classList.replace(ICONS.heart, ICONS.heartEmpty);
        }

        // en caso de existir esta variable la actualizamos
        if (window.FAVORITES_LIST) {
            window.FAVORITES_LIST = data.favorites_ids
        }

    } catch (error) {
        console.error('Error:', error);
        throw error; // Permite manejarlo fuera si se necesita
    }
}
