/// <reference path="../js/base.js" />


/**
 * Displays a custom alert message on the screen.
 * 
 * This function creates a new alert box dynamically and adds it to the alerts container.
 * The alert can be customized with a message, a predefined color, and a timeout duration.
 * It also includes a close button for manual dismissal.
 * 
 * @param {string} message - The text message to display in the alert.
 * @param {string} [color='green'] - The color of the alert.
 * @param {number} [timeout=1000] - The duration (in ms) before the alert is automatically removed.
 */
function openAlert(message, color='green', timeout=1100) {

    const alertsContainer = document.getElementById('cont__alerts');

    // Open the container
    if (alertsContainer.getAttribute('data-state') === 'closed') {
        toggleState(alertsContainer, true)
        // alertsContainer.setAttribute('data-state', 'open');
    }

    // Determine the icon class based on the color
    const iconClass = color === 'red' ? ICONS.error : ICONS.success;

    // Create a new alert box element
    const alertBox = document.createElement('div');
    alertBox.classList.add('alerts__alert');
    alertBox.innerHTML = /*html*/`
        <div class="cont-space-between text-white">
            <button class="btn text-white scale-on-touch">
                <i class="${iconClass} font-xl"></i>
            </button>
            <span>${message}</span>
            <button class="btn text-white scale-on-touch">
                <i class="${iconClass} font-xl"></i>
            </button>
        </div>
    `;

    // Predefined color mapping
    const colorMap = {
        green: "#00c01a",
        red: "#be0404e3",
        blue: "#0000ff",
        yellow: "#ffff00"
    };
    if (colorMap[color]) color = colorMap[color];
    
    // alertBox.style.color = color;
    alertBox.style.backgroundColor = color;

    alertsContainer.appendChild(alertBox);
    alertBox.classList.add('show');

    // Function to check if the alerts container is empty and close it if needed
    const checkAndCloseContainer = () => {
        // If there are no more alert elements inside the container
        if (alertsContainer.children.length === 0) {
            toggleState(alertsContainer, false)
            // alertsContainer.setAttribute('data-state', 'closed');
        }
    };

    // Remove the alert after timeout period and check container state
    setTimeout(() => {
        alertBox.remove();
        checkAndCloseContainer();
    }, timeout);

    // Add click event listeners to all close buttons in this alert
    const closeButtons = alertBox.querySelectorAll('button');
    closeButtons.forEach(button => {
        button.addEventListener('click', () => {
            alertBox.remove();
            checkAndCloseContainer();
        });
    });
}


/**
 * Displays error messages from a form submission.
 * 
 * This function iterates over an object containing form field errors and 
 * displays them as alerts with a red color. Each field may have multiple 
 * error messages associated with it.
 *
 * @param {Object} errors - An object where each key is a field name and 
 *                          its value is an array of error messages.
 * @param {number} [delay=2500] - The time in milliseconds before each alert disappears.
 */
function showErrorAlerts(errors, delay = 2500) {
    // Iterate over each field in the errors object
    for (let field in errors) {
        // Ensure the field actually belongs to the object (not from prototype)
        if (errors.hasOwnProperty(field)) {
            // Iterate over each error message for the given field
            errors[field].forEach((error) => {
                // Display an alert with the field name and its corresponding error message
                openAlert(`${field}: ${error}`, "red", delay);
            });
        }
    }
}

