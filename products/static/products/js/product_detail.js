/// <reference path="../../../../static/js/base.js" />


/**
 * Binds increment and decrement logic to quantity buttons inside the given form.
 *
 * @param {HTMLFormElement} form - The form that contains the quantity input and buttons.
 */
function eventCounters(form) {
    const addBtn = form.querySelector('.prod-detail-plus');
    const lessBtn = form.querySelector('.prod-detail-minus');
    const inputForm = form.querySelector('.prod-detail-input');

    // stupid check
    if (!addBtn || !lessBtn || !inputForm) return;

    /**
     * Increases the current quantity by 1.
     * If the current value is less than 1 or invalid, resets it to 1.
     */
    function increment() {
        const currentValue = parseInt(inputForm.value, 10) || 0;
        inputForm.value = currentValue < 1 ? 1 : currentValue + 1;
    }

    /**
     * Decreases the current quantity by 1.
     * Prevents the value from going below 1.
     */
    function decrement() {
        const currentValue = parseInt(inputForm.value, 10) || 0;
        inputForm.value = currentValue <= 1 ? 1 : currentValue - 1;
    }

    // maybe in the future apply some verify cart stock in this funcions but for now only apply in send to form
    addBtn.addEventListener('click', increment);
    lessBtn.addEventListener('click', decrement);
}

/**
 * Handles the submission of the product detail form by validating input
 * and sending an AJAX request to update the shopping cart.
 *
 * @param {HTMLFormElement} form - The form element to bind the event listener to.
 */
function eventFormProdDetail(form) {
    const inputForm = form.querySelector('.prod-detail-input');

    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const prodId = form.dataset.index; // Product ID from data attribute
        const stock = parseInt(form.dataset.stock); // Product stock from data attribute
        const value = parseInt(inputForm.value, 10) || 0;

        // Validate the input quantity
        if (isNaN(value) || value <= 0) {
            openAlert('Ingrese un numero válido.', 'red', 1000);
            return;
        }

        // Handle the form logic using a generic handler and call the cart endpoint
        await handleGenericFormBase({
            form: form,
            submitCallback: async () => {
                await endpointsCartActions({
                    productId: prodId,
                    action: 'add',
                    quantity: value,
                    stock: stock
                });
            }
        });
    });
}


function eventBtnWspProdDetail() {
    // Get the WhatsApp link element
    const btnWspLink = document.getElementById('btn-prod-wsp-link');

    // Extract the phone number from the data attribute
    const cellphone = btnWspLink.getAttribute('data-wsp');
    const productName = btnWspLink.getAttribute('data-name');
    
    // Format the phone number into a WhatsApp URL
    const whatsappUrl = formatPhoneNumber(cellphone);

    // Crea el mensaje dinámicamente con los valores del producto
    const message = `Buenos días me interesa el ${productName} 
    1- Quería consultar sobre formas de pago con tarjeta en el local?
    2- Consultar sobre tipos de envío o formas de retiro?`;

    // Si el número es válido, concatenamos la URL con el mensaje
    if (whatsappUrl) {
        const finalWhatsappUrl = `${whatsappUrl}?text=${encodeURIComponent(message)}`;
        
        // Asigna el nuevo enlace con el mensaje al atributo href
        btnWspLink.setAttribute('href', finalWhatsappUrl);

        // Assign href generic to the float btn-wsp
        const productLinkBase = document.getElementById('wsp-link');
        productLinkBase.setAttribute('href', finalWhatsappUrl);
    }
};


function productImagesChange() {

    let currentIndex = 0;

    // Get all small image containers
    const smallImages = document.querySelectorAll(".cont-lil-prod-img");
    const mainImage = document.getElementById("prod-main-image");
    const leftBtnArrow = document.querySelector(".arrow-button.left");
    const rightBtnArrow = document.querySelector(".arrow-button.right");

    if (!smallImages.length || !mainImage || !leftBtnArrow || !rightBtnArrow) return;

    /**
     * Updates the main product image and active thumbnail class
     * @param {number} index - Index of the image to show
     */
    function changeMainImage(index) {
        currentIndex = index;

        const imageElement = smallImages[index].querySelector(".img-scale-down");
        if (!imageElement) return;

        mainImage.src = imageElement.src;

        // Update active class on thumbnails
        smallImages.forEach((container, i) => {
            container.classList.toggle("active", i === index);
        });
    }

    // Assign click event to thumbnails
    smallImages.forEach((container, index) => {
        container.addEventListener("click", () => changeMainImage(index));
    });

    // Navigate to previous image
    leftBtnArrow.addEventListener("click", () => {
        const newIndex = (currentIndex - 1 + smallImages.length) % smallImages.length;
        changeMainImage(newIndex);
    });

    // Navigate to next image
    rightBtnArrow.addEventListener("click", () => {
        const newIndex = (currentIndex + 1) % smallImages.length;
        changeMainImage(newIndex);
    });

    // Initialize with the first image
    changeMainImage(currentIndex);


    /* 
        Effects for zoom images 
    */
    const zoomBtn = document.querySelector('.btn-zoom-prod');
    const overlay = document.querySelector('.prod-overlay-detail');
    const btnCloseModal = overlay.querySelector('.modal-close');
    const modal = document.querySelector('.modal-product-detail')

    const zoomedImage = modal.querySelector('#zoomedImage');
    let panzoom;

    setupToggleableElement({
        toggleButton: zoomBtn,
        closeButton: btnCloseModal,
        element: modal,
        overlay: overlay,
        onOpenCallback: () => {
            updateBackgroundImage();
        }, 
        onCloseCallback: () => {
            changeMainImage(currentIndex);
            zoomedImage.src = '';
            if (panzoom) panzoom.destroy();
        }
    });

    // get urls from images charged
    let images = [];
    smallImages.forEach(container => {
        const urlImg = container.querySelector(".img-scale-down").src;
        images.push(urlImg);
    });

    let currentScale = 0; // Rastrea el zoom actual
    let scaleZoomBtn = 0; // Rastrea el zoom actual
    const ZOOM_LEVELS = [1, 1.5, 2]; // Niveles de zoom posibles
    const DRAG_THRESHOLD = 200; // ms (tiempo mínimo para considerarse arrastre)
    let dragStartTime = 0;

    function updateBackgroundImage() {
        zoomedImage.src = images[currentIndex];
        // Destruir el panzoom anterior si existía
        if (panzoom) {
            zoomedImage.parentElement.removeEventListener('wheel', panzoom.zoomWithWheel);
            panzoom.destroy();
        }

        // Reaplicar panzoom al nuevo contenido
        panzoom = Panzoom(zoomedImage, {
          maxScale: 3,
          minScale: 1,
          contain: 'outside'
        });

        zoomedImage.parentElement.addEventListener('wheel', panzoom.zoomWithWheel);

        currentScale = 0
        scaleZoomBtn = 0
        setupZoomEvents();
    }

    function setupZoomEvents() {
        // Reiniciamos eventos previos para evitar duplicados
        zoomedImage.onclick = null;
        zoomedImage.onmousedown = null;
        zoomedImage.ontouchstart = null;

        // Evento de click (ratón y toque)
        zoomedImage.addEventListener('click', (e) => {
            if (!panzoom || (Date.now() - dragStartTime) > DRAG_THRESHOLD) {
                return;
            }
            // Rotación cíclica entre niveles de zoom
            currentScale = (currentScale + 1) % ZOOM_LEVELS.length;
            panzoom.zoom(ZOOM_LEVELS[currentScale], { 
                animate: true,
                duration: 300
            });
        });

        // Marcadores de tiempo para arrastre
        const handleDesktopStart = () => {
            dragStartTime = Date.now();
            // Temporizador para resetear (evita conflictos con Panzoom)
            setTimeout(() => {
                if (Date.now() - dragStartTime > DRAG_THRESHOLD) {
                    console.log('Drag detectado en desktop');
                }
            }, DRAG_THRESHOLD + 50);
        };

        // Usamos ambos eventos para mayor compatibilidad
        zoomedImage.addEventListener('mousedown', handleDesktopStart);
        zoomedImage.addEventListener('pointerdown', handleDesktopStart);

        zoomedImage.addEventListener('touchstart', () => {
            dragStartTime = Date.now();
        }, { passive: true });
    }

    // Hacer zoom al hacer clic en el contenedor
    const cornerZoom = overlay.querySelector('.zoom-corner');
    cornerZoom.addEventListener('click', (e) => {
        e.stopPropagation();
        
        if (panzoom) {
            // Acercar la imagen un poco, como un "scroll"
            scaleZoomBtn = (scaleZoomBtn + 1) % ZOOM_LEVELS.length;
            panzoom.zoom(ZOOM_LEVELS[scaleZoomBtn], { 
                animate: true,
                duration: 300
            });
        }
    });

    // Navegar a la imagen anterior
    const leftArrow = overlay.querySelector('.left-overlay');
    leftArrow.addEventListener('click', () => {
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        updateBackgroundImage();
    });

    // Navegar a la imagen siguiente
    const rightArrow = overlay.querySelector('.right-overlay');
    rightArrow.addEventListener('click', () => {
        currentIndex = (currentIndex + 1) % images.length;
        updateBackgroundImage();
    });

    updateBackgroundImage();
};


function descriptionProductEvent() {
    const template = document.getElementById('product-description');
    const contDesc = document.querySelector('.product-description');
    if (!template || !contDesc) return;

    /**
    * Converts textarea content to formatted HTML preview
    * @param {HTMLTextAreaElement} textarea - Input element with raw text
    * @param {HTMLElement} preview - Container for rendered preview
    */
    function updateDescription(descriptionText, preview) {
        const lines = descriptionText.split('\n').map(line => line.trim()).filter(line => line);
        const htmlLines = lines.map(line => {
            // 1. Highlight any occurrences of (**)
            line = line.replace(/\(\*\)/g, /*html*/`<b>(*)</b>`); // (*) notation
            line = line.replace(/\*\*(.+?)\*\*/g, /*html*/`<b class="font-lg">$1</b>`); // bold text

            // 2. Detect bullets at the start of the line
            if (/^\*\s+/.test(line)) {
                line = line.replace(/^\*\s+/, /*html*/`<i class="ri-git-commit-fill font-md"></i>`);    // '● '
            } else if (/^\*-\s+/.test(line)) {
                line = line.replace(/^\*-\s+/, '• ');
            }

            // 3. Special case for empty line placeholder
            if (line === '--') {
                return /*html*/`<br>`;
            }

            // 4. Return the line wrapped in a <p> tag
            return /*html*/`<p>${line}</p>`;
        });

        const finalHtml = htmlLines.join('');
        preview.innerHTML = finalHtml;
    }

    const text = template.innerHTML
    updateDescription(text, contDesc);
}


document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector('.product-detail-form');
    eventCounters(form);
    eventFormProdDetail(form);

    eventBtnWspProdDetail();
    productImagesChange();
    descriptionProductEvent();
});

/* LEGACY
    const zoomBtn = document.querySelector('.btn-zoom-prod');
    const overlay = document.querySelector('.prod-overlay-detail');
    const btnCloseModal = overlay.querySelector('.modal-close');
    const modal = document.querySelector('.modal-product-detail')

    setupToggleableElement({
        toggleButton: zoomBtn,
        closeButton: btnCloseModal,
        element: modal,
        overlay: overlay,
        onOpenCallback: () => {
            resetZoomAndDrag();
        }, 
        onCloseCallback: () => {
            resetZoomAndDrag();
            changeMainImage(currentIndex);
        }
    });

    let isZoomed = false;
    let isDragging = false;
    let startX, startY;
    let offsetX = 50, offsetY = 50;

    // get urls from images charged
    let images = [];
    smallImages.forEach(container => {
        const urlImg = container.querySelector(".img-scale-down").src;
        images.push(urlImg);
    });

    // Hacer zoom al hacer clic en el contenedor
    const cornerZoom = overlay.querySelector('.zoom-corner');
    cornerZoom.addEventListener('click', (e) => {
        e.stopPropagation();
        imageContainer.click();
    }); 

    // Actualizar la imagen de fondo
    const imageContainer = modal.querySelector('.cont-images-zoom');
    function updateBackgroundImage() {
        imageContainer.style.backgroundImage = `url(${images[currentIndex]})`;
        imageContainer.style.backgroundSize = isZoomed ? '170%' : '100%';
        imageContainer.style.backgroundPosition = `${offsetX}% ${offsetY}%`;
    }

    // Cambiar el cursor según el estado del zoom
    const zoomInIcon = overlay.getAttribute('data-zoom-in');    
    const zoomOutIcon = overlay.getAttribute('data-zoom-out');
    function updateCursor() {
        imageContainer.style.cursor = (isZoomed) ? `url('${zoomOutIcon}'), auto` : `url('${zoomInIcon}'), auto`
    }

    // Restablecer el estado de zoom y arrastre
    function resetZoomAndDrag() {
        isZoomed = false;
        isDragging = false;
        offsetX = 50;
        offsetY = 50;
        updateBackgroundImage();
        updateCursor();
    }

    imageContainer.addEventListener('click', (event) => {
        if (isZoomed && isDragging) {
            resetZoomAndDrag();
            return;
        }

        isDragging = true;
        startX = event.clientX;
        startY = event.clientY;

        isZoomed = !isZoomed;
        updateBackgroundImage();
        updateCursor();
    });

   // Función para manejar el inicio del arrastre (ratón y toque)
    function startDrag(event) {
        if (isZoomed) {
            isDragging = true;

            // Obtener las coordenadas iniciales
            if (event.type === 'touchstart') {
                event.preventDefault(); // Evitar el desplazamiento de la página
                startX = event.touches[0].clientX;
                startY = event.touches[0].clientY;
            } else {
                startX = event.clientX;
                startY = event.clientY;
            }
        }
    }

    // Función para manejar el movimiento durante el arrastre (ratón y toque)
    function moveDrag(event) {
        if (isDragging && isZoomed) {
            let clientX, clientY;

            // Obtener las coordenadas actuales
            if (event.type === 'touchmove') {
                event.preventDefault(); // Evitar el desplazamiento de la página
                clientX = event.touches[0].clientX;
                clientY = event.touches[0].clientY;
            } else {
                clientX = event.clientX;
                clientY = event.clientY;
            }

            // Calcular el desplazamiento
            const deltaX = clientX - startX;
            const deltaY = clientY - startY;

            // Actualizar la posición del fondo
            offsetX = Math.min(Math.max(offsetX + deltaX / 5, 0), 100);
            offsetY = Math.min(Math.max(offsetY + deltaY / 5, 0), 100);

            imageContainer.style.backgroundPosition = `${offsetX}% ${offsetY}%`;

            // Actualizar las coordenadas iniciales
            startX = clientX;
            startY = clientY;
        }
    }

    // Función para manejar el fin del arrastre (ratón y toque)
    function endDrag() {
        isDragging = false;
    }

    // Navegar a la imagen anterior
    const leftArrow = overlay.querySelector('.left-overlay');
    leftArrow.addEventListener('click', () => {
        currentIndex = (currentIndex - 1 + images.length) % images.length;
        resetZoomAndDrag();
        updateBackgroundImage();
    });

    // Navegar a la imagen siguiente
    const rightArrow = overlay.querySelector('.right-overlay');
    rightArrow.addEventListener('click', () => {
        currentIndex = (currentIndex + 1) % images.length;
        resetZoomAndDrag();
        updateBackgroundImage();
    });


// Eventos para ratón
    imageContainer.addEventListener('mousedown', startDrag);
    window.addEventListener('mousemove', moveDrag);
    window.addEventListener('mouseup', endDrag);

    // Eventos para toque
    imageContainer.addEventListener('touchstart', startDrag, { passive: false });
    window.addEventListener('touchmove', moveDrag, { passive: false });
    window.addEventListener('touchend', endDrag);
*/