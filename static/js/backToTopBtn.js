/// <reference path="../js/app_config.js" />
/// <reference path="../js/base.js" />
/// <reference path="../js/utils.js" />
/// <reference path="../js/overlay_modal.js" />


/**
 * Smoothly scrolls the window to the top of the page.
 * @function backToTheTop
 */
function backToTheTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
}


/**
 * Shows or hides the "Back to Top" button and safely adds or removes
 * its click event handler as needed.
 *
 * This ensures that the event is only attached once and removed when
 * the button is hidden, preventing duplicate handlers or memory leaks.
 *
 * @param {boolean} show - Whether to display the button.
 * @param {HTMLElement} btn/backToTopBtn - The Back to Top button element.
 *
 * Example usage:
 *   toggleBackToTopButton(true, document.getElementById('backToTopBtn'));
 */
function toggleBackToTopButton(show, btn) {
    if (show) {
        btn.classList.add("show");

        if (!btn.hasAttribute('data-event-added')) {
            btn.addEventListener("click", backToTheTop);
            btn.setAttribute('data-event-added', 'true');
        }
    } else {
        btn.classList.remove("show");

        if (btn.hasAttribute('data-event-added')) {
            btn.removeEventListener("click", backToTheTop);
            btn.removeAttribute('data-event-added');
        }
    }

    // Enable or disable pointer events based on visibility
    btn.style.pointerEvents = show ? "all" : "none";
}


/**
 * Initializes the scroll spy for the Back to Top component.
 * Tracks scroll progress to update the SVG stroke-dashoffset and 
 * manages visibility based on page position and overlay state.
 * @function eventBackToTopBtn
 */
function eventBackToTopBtn() {
    const backToTopBtn = document.getElementById("backToTop");
    if (!backToTopBtn) return; // stupid check

    const progressCircle = backToTopBtn.querySelector(".progress circle");
    const circumference = 126; // Circumference of the SVG circle

    /**
     * Handles the scroll event to show or hide the button
     * and update the progress indicator circle.
     */
    window.addEventListener("scroll", function () {

        // Hide button if an overlay/modal is active
        if (typeof overlayClickListener !== 'undefined' && overlayClickListener) {
            toggleBackToTopButton(false, backToTopBtn); 
            return;
        }
        
        let scrollTop = window.scrollY || document.documentElement.scrollTop; // Current scroll position
        let scrollHeight = document.documentElement.scrollHeight - window.innerHeight; // Total scrollable height

        // Avoid division by zero on very short pages
        // Calculates the scroll percentage
        const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;

        // Show or hide the button based on scroll position
        toggleBackToTopButton(scrollTop > 100, backToTopBtn);
        
        // Adjust the progress circle stroke based on the scroll percentage
        // you must change values in base.html too for apply changes
        // 126 is the full circumference of the circle
        let dashOffset = circumference - (progress / 100) * circumference; 
        progressCircle.style.strokeDashoffset = dashOffset;
    }, { passive: true });
}
