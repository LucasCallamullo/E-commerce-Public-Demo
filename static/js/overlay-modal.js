

/// <reference path="../js/base.js" />
/// <reference path="../js/backToTopBtn.js" />


/** Example usage for simple btn with modal    (Complete example in users / admin_profile.js):
    setupToggleableElement({
        toggleButton: document.getElementById('btn-open'),
        closeButton: document.getElementById('btn-close'),
        element: document.getElementById('modal'),
        overlay: document.getElementById('overlay'),
        onOpenCallback: () => console.log('Menu opened!') // Optional callback function
        onCloseCallback: () => console.log('Menu closed!') // Optional callback function
    });

/** Example usage for a modal with delegation
    const modalForm = document.querySelector('#form-new-product');
    const modalClose = document.querySelector('#form-new-product-close');
    const overlay = document.querySelector('#overlay-new-product');

    // Configura el modal UNA VEZ y obtén el método `open`
    const { open } = setupToggleableElement({
        closeButton: modalClose,
        element: modalForm,
        overlay: overlay,
        onOpenCallback: ({ params }) => {
            const { row } = params;
            // Custom Logic if u want ... example
            initInputImage(modalForm);
            initModalCancelBtns(modalForm, modalClose);
            calculateDiscountSubtotal(modalForm);
        },
        onCloseCallback: () => {
            // Custom Logic if u want
        }
    });

    // Delegación de eventos en tableSection
    tableSection.addEventListener('click', (e) => {
        const row = e.target.closest('.row-table');
        if (!row) return;

        // Abre el modal con datos de la fila clickeada
        open({ row });
    });
 * 
 * 
 */
class OverlayManager {
    // Static stack to store all currently opened overlays
    static overlayStack = [];
    // Flag to ensure global event listeners are only added once
    static isGlobalListenersAdded = false;

    constructor(overlay) {
        // Store the reference to the specific overlay element being managed
        this.overlay = overlay;
    }

    /**
     * Initializes the global event listeners for overlay handling.
     * This is executed only once for the whole page lifecycle.
     */
    static initGlobalListeners() {
        // 1. Prevent adding the listeners multiple times
        if (OverlayManager.isGlobalListenersAdded) return;

        // 2. Listen for clicks on the document
        document.addEventListener('click', (e) => {
            // Get the most recently opened overlay (top of the stack)
            const topOverlay = OverlayManager.overlayStack.at(-1);
            if (!topOverlay) return; // Exit if no overlays are open

            // If the click happened directly on the overlay (not its children)
            if (topOverlay === e.target) {
                // Call the close callback for this overlay
                topOverlay.__closeCallback?.();
            }
        });

        // 3. Listen for the ESC key press
        document.addEventListener('keydown', (e) => {
            const topOverlay = OverlayManager.overlayStack.at(-1);
            // If ESC is pressed and an overlay is open
            if (e.key === "Escape" && topOverlay) {
                e.preventDefault(); // Prevent default ESC behavior
                topOverlay.__closeCallback?.(); // Close the overlay
            }
        });

        // 4. Listen for browser back button navigation
        window.addEventListener('popstate', () => {
            const topOverlay = OverlayManager.overlayStack.at(-1);
            if (topOverlay) {
                // Push a fake history state so that the back button triggers popstate again
                history.pushState(null, null, window.location.pathname);
                // history.pushState({ hasOverlay: true }, null, window.location.pathname);

                // Close the current top overlay
                topOverlay.__closeCallback?.();
            }
        });

        // 5. Mark the global listeners as added
        OverlayManager.isGlobalListenersAdded = true;
    }

    /**
     * Opens the overlay and attaches a close callback.
     * @param {Function} onCloseCallback - Function to call when the overlay is closed
     */
    open(onCloseCallback) {
        // Step 1: Ensure global listeners are initialized
        OverlayManager.initGlobalListeners();
        
        // Step 2: Attach the close callback directly to the overlay element
        this.overlay.__closeCallback = onCloseCallback;

        // Step 3: Push the overlay onto the stack
        OverlayManager.overlayStack.push(this.overlay);

        // Step 4: Show the overlay
        this.overlay.classList.add('show');
        
        // Step 5: Only push a history state if this is the first overlay
        if (OverlayManager.overlayStack.length === 1) {
            history.pushState({ hasOverlay: true }, null, window.location.pathname);
        }
    }

    /**
     * Closes the overlay and updates the stack/history state.
     */
    close() {
        // Step 1: Find the overlay in the stack
        const index = OverlayManager.overlayStack.indexOf(this.overlay);
        if (index === -1) return; // Exit if overlay not found in stack

        // Step 2: Remove overlay from the stack
        OverlayManager.overlayStack.splice(index, 1);

        // Step 3: Remove the close callback reference
        delete this.overlay.__closeCallback;

        // Step 4: Hide the overlay
        this.overlay.classList.remove('show');

        // Step 5: If no overlays remain open, go back in browser history
        if (OverlayManager.overlayStack.length === 0) {
            history.back();
        }
    }
}


/**
 * Sets up a toggleable UI element (such as a modal or mobile menu) with automatic event management.
 * 
 * @param {Object} options - Configuration options for the toggleable element.
 * @param {HTMLElement} options.toggleButton - The button that opens the element.
 * @param {HTMLElement} options.closeButton - The button that closes the element.
 * @param {HTMLElement} options.element - The element to be shown/hidden (e.g., a modal or menu).
 * @param {HTMLElement} options.overlay - The overlay displayed behind the element.
 * @param {boolean} [options.flagStop=false] - Optional flag to stop event propagation when opening (default is false).
 * @param {Function} [options.onOpenCallback=null] - Optional function to execute when the element is opened.
 * @param {Function} [options.onCloseCallback=null] - Function to execute on close
 */

let overlayClickListener = false;  // Holds the current click listener for the overlay
function setupToggleableElement(options) {
    const { 
        toggleButton = null,
        closeButton, 
        element, 
        overlay, 
        flagStop = false, 
        onOpenCallback = null, 
        onCloseCallback = null,
        shouldOpen = null,
        customParams = {}
    } = options;

    if (!closeButton || !element || !overlay) {
        console.error('Missing required elements');
        return;
    }

    // const overlayManager = new OverlayManager();
    const overlayManager = new OverlayManager(overlay);

    /**
     * Closes the toggleable element and overlay.
     * Also removes the click event listener from the close button to prevent memory leaks.
     * 
     * @param {Function} closeHandler - The function to remove from the close button's click event.
     */
    const closeHandler = () => {
        // if (onCloseCallback) onCloseCallback();
        if (onCloseCallback) onCloseCallback(customParams);
        toggleState(element);
        // overlayManager.close(overlay);
        overlayManager.close();
        overlayClickListener = false;
    };

    /**
     * Opens the toggleable element and sets up necessary event listeners for closing.
     * Also manages event propagation if flagStop is enabled.
     * 
     * @param {Event} event - The click event from the toggle button.
     */
    // const openHandler = (e) => {
    const openHandler = (e, customData = {}) => {
        if (flagStop) e.stopPropagation();
        
        if (onOpenCallback) {
            onOpenCallback({ 
                event: e, 
                params: { ...customParams, ...customData }
            });
        }

        // overlayManager.open(overlay, closeHandler);
        overlayManager.open(closeHandler);
        toggleState(element);
        overlayClickListener = true;

        // Listener para cerrar (siempre)
        if (!closeButton.__hasCloseListener) {
            closeButton.addEventListener('click', closeHandler);
            closeButton.__hasCloseListener = true;
        }
    };

    // Si hay toggleButton, agregamos listener (para compatibilidad)
    if (toggleButton && !toggleButton.__hasOpenListener) {
        // toggleButton.addEventListener('click', (e) => openHandler(e));
        toggleButton.addEventListener('click', (e) => {
            if (shouldOpen && !shouldOpen(e)) return; 
            openHandler(e);
        });
        toggleButton.__hasOpenListener = true;
    }

    // Permite abrir el modal manualmente
    return {
        open: (customData = {}) => openHandler(null, customData)  // Sin evento, con datos dinámicos
    };
}


window.addEventListener('load', () => {
    // Check if the current browser history state has the property "hasOverlay" set to true
    // Navigate back to the previous history entry
    if (history.state?.hasOverlay) history.back();
});
