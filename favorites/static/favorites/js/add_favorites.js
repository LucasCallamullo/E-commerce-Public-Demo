


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

        // Alternar clases visuales
        const isLiked = btn.classList.contains("liked");
        const icon = btn.querySelector('i');

        if (isLiked) {
            btn.classList.remove("liked");
            icon.classList.replace(ICONS.heart, ICONS.heartEmpty);
            openAlert('Producto eliminado como Favorito.', 'red', 1500);
        } else {
            btn.classList.add("liked");
            icon.classList.replace(ICONS.heartEmpty, ICONS.heart);
            openAlert('Producto agregado como Favorito!', 'green', 1500);
        }

    } catch (error) {
        console.error('Error:', error);
        throw error; // Permite manejarlo fuera si se necesita
    }
}
