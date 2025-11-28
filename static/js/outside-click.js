/// <reference path="../js/base.js" />
/// <reference path="../js/alerts.js" />


/* 
    EXAMPLE TO USE: 
    setupClickOutsideClose({
        triggerElement: btn,
        targetElement: menu,
        customToggleFn: () => {
            const isExpanded = toggleState(menu);
            arrowDrop.classList.toggle("rotate", isExpanded);
            return isExpanded
        }
    });
*/
// ============================================================================
//  ClickOutsideManager: Singleton to track multiple dropdowns or menus
//  and handle closing them when clicking outside or pressing Escape.
//  Only ONE listener on document is used for all.
// ============================================================================
const ClickOutsideManager = (() => {
    // Store all active elements to track
    const trackedElements = new Set();

    /**
     * Handles document click:
     * For each tracked dropdown, if it's open and click is outside, call its close method.
     */
    function handleClickOutside(event) {
        trackedElements.forEach(({ trigger, target, close }) => {
            const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
            if (!isExpanded) return; // Skip if not open

            const clickedOutside =
                !trigger.contains(event.target) &&
                !target.contains(event.target);

            if (clickedOutside) {
                close(); // Close this dropdown
            }
        });
    }

    /**
     * Handles Escape key:
     * Closes all tracked dropdowns.
     */
    function handleEscape(event) {
        if (event.key !== 'Escape') return;
        trackedElements.forEach(({ close }) => close());
    }

    // Add global listeners ONCE
    document.addEventListener('click', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return {
        /**
         * Register a dropdown/menu when opened.
         * @param {Object} param0 - Object containing trigger, target, and close()
         */
        register({ trigger, target, close }) {
            trackedElements.add({ trigger, target, close });
        },
        /**
         * Unregister a dropdown/menu when closed.
         * @param {Object} entry - The same object previously registered.
         */
        unregister(entry) {
            trackedElements.delete(entry);
        }
    };
})();


/**
 * Sets up a dropdown or menu to toggle open/close,
 * and automatically close when clicking outside or pressing Escape.
 * 
 * @param {HTMLElement} triggerElement - Button or trigger to toggle open/close
 * @param {HTMLElement} targetElement - The dropdown/menu element to show/hide
 * @param {Function} [onToggle=() => {}] - Optional callback when toggled (receives new state: true=open, false=closed)
 * 
 *  EXAMPLE
 *  setupClickOutsideClose({
        triggerElement: btn,
        targetElement: menu,
        customToggleFn: () => {
            const isExpanded = toggleState(menu);
            arrowDrop.classList.toggle("rotate", isExpanded);
            return isExpanded
        }
        shouldStopPropagation = (e) => {
            // optional return true or false custom with e target     
        }
    });
 */
function setupClickOutsideClose({
    triggerElement,
    targetElement,
    customToggleFn = () => {},
    shouldStopPropagation = () => true,
} = {}) {
    let entry = null;

    function toggleDropdown(flagStop) {
        if (!flagStop) return;

        const isExpanded = triggerElement.getAttribute('aria-expanded') === 'true';
        const newState = !isExpanded;
        triggerElement.setAttribute('aria-expanded', newState);
        
        const isOpen = customToggleFn();

        if (isOpen) {
            entry = {
                trigger: triggerElement,
                target: targetElement,
                close: () => {
                    // Cierra usando tu propia lógica o la logica comun de data-state
                    customToggleFn();

                    triggerElement.setAttribute('aria-expanded', 'false');
                    ClickOutsideManager.unregister(entry);
                }
            };
            ClickOutsideManager.register(entry);
        } else {
            ClickOutsideManager.unregister(entry);
        }
    }

    triggerElement.addEventListener("click", (e) => {
        let flagStop = shouldStopPropagation(e)
        if (flagStop) {
            e.stopPropagation();
        }
        toggleDropdown(flagStop);
    });

    targetElement.addEventListener("click", (e) => {
        if (shouldStopPropagation(e)) {
            e.stopPropagation();
        }
    });
}
