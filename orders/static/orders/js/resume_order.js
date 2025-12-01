/// <reference path="../../../../static/js/base.js" />
/// <reference path="../../../../static/js/forms.js" />
/// <reference path="../../../../static/js/utils.js" />
/// <reference path="../../../../static/js/overlay-modal.js" />


/**
 * Attaches change event listeners to all radio inputs with name "payment".
 * When a radio button is selected, it updates the display of all elements
 * with the class "payment-method" and shows a success alert.
 *
 * @param {HTMLFormElement} form - The form element containing the payment options.
 */
function paymentRadio(containerMain, form) {

    // Select all elements meant to display the selected payment method
    const paymentSpans = containerMain.querySelectorAll('.payment-method');

    // input a cambiar su valor
    const inputForm = form.querySelector('input[type="hidden"][name="payment_method_id"]')

    // Contenedor padre de los radios
    const paymentsContainer = containerMain.querySelector('#payment-methods-section'); 
    paymentsContainer.addEventListener('change', (event) => {
        // Verificar si el elemento que disparó el evento es un radio button
        if (event.target.matches('input[type="radio"][name="payment"]')) {
    
            // When a radio is selected, update all display spans
            paymentSpans.forEach(display => {
                display.textContent = event.target.value;
            });

            // Show success alert with the selected payment method
            openAlert(`Método de pago actualizado a ${event.target.value}.`, 'green', 2000);

            inputForm.value = event.target.dataset.index || '0';
        };
    });
}


/**
 * Attaches change event listeners to all radio inputs with name "ship".
 * Updates shipping information, displays the correct form section,
 * updates price display, and shows a confirmation alert.
 *
 * @param {HTMLFormElement} form - The form element containing shipping options and sections.
 */
function shippingRadio(containerMain, form) {


    // Select all elements meant to display the selected shipping method
    const shipSpans = containerMain.querySelectorAll('.shipment-method');

    // Element where the shipping price is displayed
    const shipPriceSpan = containerMain.querySelector('.shipment-price');

    // Sections to show or hide depending on the selected shipping method
    const retireSection = form.querySelector('#retire-form');
    const shippinSection = form.querySelector('#shippin-form'); 
    
    // input a cambiar el valor 
    const inputForm = form.querySelector('input[type="hidden"][name="shipping_method_id"]');

    // Contenedor padre de los radios
    const shippingContainer = containerMain.querySelector('#shipping-methods-section'); 


    shippingContainer.addEventListener('change', (event) => {
        // Verificar si el elemento que disparó el evento es un radio button
        if (event.target.matches('input[type="radio"][name="ship"]')) {
            // Get the dataset index (used to determine selected shipping method)
            const shipId = event.target.dataset.index || 0;

            // Toggle visibility of form sections based on selected shipping method
            if (shipId === '1') {
                retireSection.style.display = 'grid';
                shippinSection.style.display = 'none';
                // Activar required solo en la sección de retiro
                scrollToSection(retireSection);
                toggleRequiredInputs(retireSection, true);
                toggleRequiredInputs(shippinSection, false);
            } else {
                retireSection.style.display = 'none';
                shippinSection.style.display = 'grid';
                // Activar required solo en la sección de envío
                scrollToSection(shippinSection);
                toggleRequiredInputs(retireSection, false);
                toggleRequiredInputs(shippinSection, true);
            }

            // Get and format the shipping price from data-price attribute
            const price = formatNumberWithPoints(event.target.dataset.price);
            shipPriceSpan.textContent = price === 'Gratis' ? price : `$ ${price}`;

            // Update all spans showing the selected shipping method
            shipSpans.forEach(display => {
                display.textContent = event.target.value;
            });

            // agregamos dataset al form para usar despues antes de enviar
            inputForm.value = shipId || '0';
            
            openAlert(`Método de envío actualizado a ${event.target.value}.`, 'green', 2000);
        }
    });

    // esta funcion pone en required o no los input de cada formulario 
    // en especifico segun corresponda
    function toggleRequiredInputs(section, isRequired) {
        const inputs = section.querySelectorAll('.input-required');
        inputs.forEach(input => {
            if (isRequired) {
                input.setAttribute('required', 'required');
            } else {
                input.removeAttribute('required');
            }
        });
    }
}


/**
 * Validates and submits the order form.
 * Gathers form data, ensures that a payment and shipping method are selected,
 * then sends the data via POST in JSON format.
 *
 * @param {HTMLFormElement} form - The form element containing order details.
 * @returns {Promise<string|undefined>} - Returns the order ID on success, or undefined if failed.
 */
async function validFormOrder(form) {

    // Build FormData and convert to JSON
    const formData = new FormData(form);
    const paymentId = formData.get('payment_method_id');
    const shippingId = formData.get('shipping_method_id');

    if (paymentId === '0' || shippingId === '0') {
        openAlert(
            `Elija correctamente un método de ${(paymentId == '0') ? 'pago' : 'envío'}.`, 
            'orange', 1500
        );
        return;
    }    
    const jsonData = Object.fromEntries(formData.entries());
    const url = window.TEMPLATE_URLS.validOrder

    try {
        // Send the POST request to the server with JSON data
        const response = await fetch(url, { 
            method: 'POST',
            body: JSON.stringify(jsonData),
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            }
        });

        const data = await response.json(); 

        // If response is not ok, handle different types of errors
        if (!response.ok) {    
            openAlert(data.detail || 'No hay suficiente Stock.', 'red', 1500);
            return;
        }

        // On success, notify and return order ID
        openAlert('Pedido guardado, complete su pago para finalizar!', 'green', 1500);
        return data.order_id;

    } catch (error) {
        console.error('Error:', error);
        openAlert('Error al procesar la solicitud. Intenta nuevamente.', 'red', 2000);
    }
}


/**
 * Handles the setup and validation logic for the order form modal.
 * @param {HTMLFormElement} form - The order form element.
 */
function eventFormOrder(containerMain, form) {
    const modal = containerMain.querySelector('.modal-order');
    const btnClose = modal.querySelector('.btn-close');

    const overlay = containerMain.querySelector('#overlay-order');
    const btnOpenModal = containerMain.querySelector('#btn-open-order');

    let flag = false;

    // Set up modal toggle behavior with validation before opening
    setupToggleableElement({
        toggleButton: btnOpenModal,
        closeButton: btnClose,
        element: modal,
        overlay: overlay,
        shouldOpen: (e) => {
            flag = flagsOrdersConfirm();
            return true;
        },
    });

    const confirmButton = form.querySelector('#btn-confirm-form');
    
    // First confirm button: validates and opens modal if valid
    confirmButton.addEventListener('click', () => {
        if (!flag) {
            flag = flagsOrdersConfirm();
            if (!flag) return;
        }
        btnOpenModal.click();
    });

    const confirmButtonModal = containerMain.querySelector('#btn-confirm-order-modal');
    const btnFormSubmit = form.querySelector('#btn-order-submit');
    
    // Second confirm button inside modal: closes modal and submits form if valid
    confirmButtonModal.addEventListener('click', () => {
        if (!flag) {
            flag = flagsOrdersConfirm();
            if (!flag) return;
        }
        btnClose.click();
        btnFormSubmit.click();
    });

    const paymentSection = containerMain.querySelector('#payment-methods-section');
    const shippingSection = containerMain.querySelector('#shipping-methods-section');

    /**
     * Validates if a radio input in a section is selected properly.
     * @param {string} name - The name of the hidden input group.
     * @param {HTMLElement} section - The section to scroll to if invalid.
     * @param {string} errorMessage - The error message to show if invalid.
     * @returns {boolean}
     */
    function validateRadioSelection(name, section, errorMessage) {
        const input = form.querySelector(`input[name="${name}"]`);
        if (!input || input.value === '0') {
            openAlert(errorMessage, 'red', 2000);
            scrollToSection(section);
            return false;
        }
        return true;
    }

    /**
     * Confirms both payment and shipping method are selected properly.
     * Sets `flag` to true if both are valid.
     * @returns {boolean}
     */
    function flagsOrdersConfirm() {
        if (
            !flag &&
            validateRadioSelection("payment_method_id", paymentSection, "No seleccionaste un Método de Pago.") &&
            validateRadioSelection("shipping_method_id", shippingSection, "No seleccionaste un Método de Envío.")
        ) {
            flag = true;
        }
        return flag;
    }
};


document.addEventListener('DOMContentLoaded', () => {

    const containerMain = document.getElementById('main-base');
    const form = containerMain.querySelector('#form-order');
    let order_id;

    // Handle form submission
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Call the generic handler for form submission (includes animation, validation, and redirect)
        await handleGenericFormBase({
            form: form, 
            submitCallback: async () => {
                try {
                    order_id = await validFormOrder(form);
                } catch (err) {
                    console.log('Validation error:', err);
                }
            },
            closeCallback: () => {
                // Redirect user to the payment page with the correct order ID in the URL
                if (!order_id) return; 
                const url = window.TEMPLATE_URLS.paymentPage.replace('{order_id}', `${order_id}`);
                window.location.href = url;
            },
            flag_anim: true,
            time_anim: 1500
        });
    });

    // Initialize logic related to selecting a payment method
    paymentRadio(containerMain, form);

    // Initialize logic related to selecting a shipping method
    shippingRadio(containerMain, form);

    // Initialize additional event handlers for the order form
    eventFormOrder(containerMain, form);

    // renderizar inicialmente la table dentro del modal a partir de window.CART_DATA
    renderTableModal(containerMain);
});
