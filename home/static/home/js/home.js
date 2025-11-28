/// <reference path="../../../../products/static/products/js/components/carousel_products.js" />


window.addEventListener('DOMContentLoaded', () => {
    /* Swiper header */
    var swiperHeader = new Swiper('.swiper-container', {
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

    // esta function crea en el dom todo las listas de productos por categoría
    const container = document.getElementById('cont-swipers-home');
    createCarouselCards(container);
});
