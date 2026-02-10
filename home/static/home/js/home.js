/// <reference path="../../../../products/static/products/js/components/carousel_products.js" />
/// <reference path="../../../../products/static/products/js/components/cards_products.js" />





function initBanners(selector) {
    /* Swiper header */
    var swiperHeader = new Swiper(`${selector}`, {
        loop: true, // Infinite loop to continuously cycle through slides
        autoplay: {
            delay: 2500, // Time interval between slides (in milliseconds)
            disableOnInteraction: false, // Keep autoplay active even after user interaction
        },
        grabCursor: true, // Show grab cursor when hovering over the slider
        slidesPerView: 1, // Ensures only one slide is displayed at a time
        spaceBetween: 0, // Space between slides (adjust if needed)
        navigation: {
            nextEl: '.swiper-button-next', // Selector for the next slide button
            prevEl: '.swiper-button-prev', // Selector for the previous slide button
        },
        pagination: {
            el: '.swiper-pagination', // Selector for pagination bullets
            clickable: true, // Allows clicking on pagination bullets to navigate
        },
    });
}


function initB(selector) {
    var swiperGrid = new Swiper(`${selector}`, {
        // 1. Definimos las columnas
        slidesPerView: 3,
        
        // 2. Definimos las filas
        autoplay: {
            delay: 2500, // Time interval between slides (in milliseconds)
            disableOnInteraction: false, // Keep autoplay active even after user interaction
        },
        grabCursor: true, // Show grab cursor when hovering over the slider
        grid: {
            rows: 2,
            fill: 'row', // Rellena de izquierda a derecha
        },
        
        // 3. Espaciado
        spaceBetween: 20,

        // 4. Otras opciones que ya tenías
        navigation: {
            nextEl: '#btn-next-offers', // Selector for the next slide button
            prevEl: '#btn-prev-offers', // Selector for the previous slide button
        },
        
        // Nota: En modo GRID, 'loop: true' no está soportado oficialmente 
        // y suele romper el layout. Mejor dejarlo en false.
        loop: true,

        breakpoints: {
            992: {
                slidesPerView: 3,
                grid: { rows: 2 }
            },
            0: {
                slidesPerView: 1,
                grid: { rows: 2 }
            }
        }
    });
}


window.addEventListener('DOMContentLoaded', () => {
    
    initBanners('.cont-headers');
    initBanners('.cont-banners');

    const offersContainer = document.querySelector('.swiper-offers');
    initB('.swiper-offers');

    // esta function crea en el dom todo las listas de productos por categoría
    const container = document.getElementById('cont-swipers-home');

    // Attach product events only once to the container (static delegation)
    if (!container._hasInitEvents) {
        // carousel_cards.js
        initSwipers(container);    // Initialize Swiper instances for all inserted carousels

        productCardFormsEvents(container); // Form actions (e.g., add to cart)
        productCardModalEvent(container);  // Modal opening actions
        productCardModalEvent(offersContainer);  // Modal opening actions

        container._hasInitEvents = true;
    }

    // setear datos iniciales 
    window.PRODUCT_STORE.setData(JSON.parse(
        document.getElementById("products-data").textContent
    ));

    // setear data necesaria para los modales
    window.CATEGORIES_LIST = JSON.parse(
        document.getElementById("categories-data").textContent
    );

    window.BRANDS_LIST = JSON.parse(
        document.getElementById("brands-data").textContent
    );
});
