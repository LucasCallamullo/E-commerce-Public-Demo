/// <reference path="../js/base.js" />


/**
 * Smoothly scrolls the page back to the top.
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
 * @param {HTMLElement} backToTopBtn - The Back to Top button element.
 *
 * Example usage:
 *   toggleBackToTopButton(true, document.getElementById('backToTopBtn'));
 */
function toggleBackToTopButton(show, backToTopBtn) {
    if (show) {
        backToTopBtn.classList.add("show");

        if (!backToTopBtn.hasAttribute('data-event-added')) {
            backToTopBtn.addEventListener("click", backToTheTop);
            backToTopBtn.setAttribute('data-event-added', 'true');
        }
    } else {
        backToTopBtn.classList.remove("show");

        if (backToTopBtn.hasAttribute('data-event-added')) {
            backToTopBtn.removeEventListener("click", backToTheTop);
            backToTopBtn.removeAttribute('data-event-added');
        }
    }

    // Enable or disable pointer events based on visibility
    backToTopBtn.style.pointerEvents = show ? "all" : "none";
}


document.addEventListener('DOMContentLoaded', () => {
    const backToTopBtn = document.getElementById("backToTop");
    const progressCircle = backToTopBtn.querySelector(".progress circle");

    /**
     * Handles the scroll event to show or hide the button
     * and update the progress indicator circle.
     */
    window.addEventListener("scroll", function () {

        // Oculta el botón si el overlay está abierto
        if (overlayClickListener) {
            toggleBackToTopButton(false, backToTopBtn); 
            return;
        }
        
        let scrollTop = window.scrollY || document.documentElement.scrollTop; // Current scroll position
        let scrollHeight = document.documentElement.scrollHeight - window.innerHeight; // Total scrollable height
        let progress = (scrollTop / scrollHeight) * 100; // Calculates the scroll percentage

        // Show or hide the button based on scroll position
        toggleBackToTopButton(scrollTop > 100, backToTopBtn);
        
        // Adjust the progress circle stroke based on the scroll percentage
        // you must change values in base.html too for apply changes
        let dashOffset = 126 - (progress / 100) * 126; // 126 is the full circumference of the circle
        progressCircle.style.strokeDashoffset = dashOffset;
    }, { passive: true });
});
