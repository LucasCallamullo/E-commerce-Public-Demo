/// <reference path="../../../../../static/js/base.js" />
/// <reference path="../../js/logic/cards_products.js" />


function initSwipers(container) {

    // Loop through all swiper containers with the class "swiper-products"
    const swipers = container.querySelectorAll('.swiper-products')
    swipers.forEach((swiperContainer, index) => {

        // Count how many slides this container has
        const slides = swiperContainer.querySelectorAll('.swiper-slide').length;

        // Minimum slides needed for loop to work properly.
        // For 'slidesPerView: auto', a practical safe value is 4 or more.
        const shouldLoop = slides >= 4;

        // Initialize Swiper with dynamic loop value
        const swiper = new Swiper(`#swiper-${index}`, {
            loop: shouldLoop,    // Evita acumulación de slides mal posicionados
            autoplay: {
                delay: 6000,
                disableOnInteraction: false,
            },
            slidesPerView: "auto",    // Se ajusta con el CSS
            centeredSlides: false,    // Evita que los slides se centren incorrectamente
            grabCursor: true,
            navigation: {
                nextEl: `#next-${index}`,
                prevEl: `#prev-${index}`,
            },
        });
    });
}


function renderSwiperCategory(category, counter) {
    const swiperHtml = /*html*/`
        <div class="carousel-category">
            <div class="cont-space-between cont_carousel__title">
                <div class="d-flex justify-start px-2 h-100 carousel__title">
                    <a class="font-md text-white bolder" href="#"> 
                        ${category}
                    </a>
                </div>
        
                <div class="d-flex gap-1"> 
                    <button class="swiper-button-prev-product" id="prev-${counter}">
                        <i class="ri-arrow-left-s-line font-lg"></i>
                    </button>
                    <button class="swiper-button-next-product" id="next-${counter}">
                        <i class="ri-arrow-right-s-line font-lg"></i>
                    </button>
                </div>
            </div>
        
            <div class="swiper-products" id="swiper-${counter}">
                <div class="swiper-wrapper">  </div>
            </div>
        </div>
    `.trim();

    const container = document.createElement('div');
    container.innerHTML = swiperHtml;

    // este es el contenedor que vamos a completar con cartas de forma dinamica
    const swiperWrapper = container.querySelector('.swiper-wrapper');
    return { element: container.firstElementChild, swiperWrapper };
}


/* esto se crea parcialmente ya que es parte del modulo pagination orginalmente, pero es necesario
este objeto para utilizar los modales */
window.ProductStore = {
    data: [],
    setData(newData) {
        /**
         * Sets the internal product data store.
         *
         * @param {Array} newData - An array of product objects to be stored.
         */
        this.data = newData;
    },
    getData() {
        /**
         * Returns the current product data.
         *
         * @returns {Array} - The array of stored product objects.
         */
        return this.data;
    },
}


/**
 * Creates and renders carousel cards inside a given container.
 * 
 * - Takes a container element and populates it with product category carousels.
 * - Uses `window.productList` (category → products mapping) to generate each carousel.
 * - For each category:
 *      1. Creates a Swiper wrapper for that category.
 *      2. Appends rendered product cards into the Swiper slides.
 *      3. Adds the generated category element into a DocumentFragment for batch insertion.
 * - Saves all products into `ProductStore` for global access.
 * - Initializes Swiper instances for the created carousels.
 * - Adds product-related events only once (avoids duplicate bindings).
 * 
 * @param {HTMLElement} container - The DOM element where the carousels will be inserted.
 * @param {list} products - optional params in some views to use with a list fetch
 */
function createCarouselCards(container, products=null) {
    
    // Validate container existence
    if (!container) {
        console.error('container no encontrado / container not found');
        return;
    }

    // Check if global product list is available
    if (window.productList) {
        const fragment = document.createDocumentFragment(); // Temporary holder to reduce reflows
        let counter = 0;                                    // Keeps track of category index
        let listToSet = [];                                 // Will hold all products for ProductStore

        // Loop through each category and its products
        for (const [category, products] of Object.entries(window.productList)) {
            // Create the Swiper container & wrapper for this category
            const { element, swiperWrapper } = renderSwiperCategory(category, counter);

            // Render and append each product card
            products.forEach(product => {
                swiperWrapper.appendChild(renderCards(product, true));
                listToSet.push(product); // Store in global list
            });

            // Append the completed carousel to the fragment
            fragment.appendChild(element);
            counter++;
        }

        // Save all products into global ProductStore
        ProductStore.setData(listToSet);

        // Insert all carousels into the container in a single operation
        container.appendChild(fragment);

        // Initialize Swiper instances for all inserted carousels
        initSwipers(container);
    }

    if (products) {
        // this function is from profile/js/tabs/tab_favorites.js
        if (typeof createTabfavorites === 'function') {
            createTabfavorites(container, products);
        }
    }

    // Attach product events only once to the container (static delegation)
    if (!container._hasInitEvents) {
        productCardFormsEvents(container); // Form actions (e.g., add to cart)
        productCardModalEvent(container);  // Modal opening actions
        container._hasInitEvents = true;
    }
}
