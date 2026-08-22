/**
 * @file errors.js
 * @description Centralized error management system for Frontend and Backend interactions.
 * Provides a hierarchy of custom Error classes to standardize UI feedback.
 */

/**
 * Base Application Error.
 * Extends the native Error class to include UI-specific metadata like colors and timing.
 * @extends Error
 */
class AppError extends Error {

    /**
     * @param {Object} params - Error configuration.
     * @param {string} params.message - Human-readable error message.
     * @param {string} [params.color='red'] - Feedback color for UI alerts.
     * @param {number} [params.time=1500] - Duration (ms) the alert should be visible.
     * @param {string} [params.field=''] - The 'name' attribute of the related HTML input.
     */
    constructor({ message, color = 'red', time = 1500, field = '' } = {}) {
        super(message);
        this.color = color;
        this.time = time;
        this.field = field;

        // Maintains a clean stack trace by hiding the constructor call (V8 engines)
        if (Error.captureStackTrace) {
            Error.captureStackTrace(this, this.constructor);
        }
    }
}


/**
 * Server-side / Backend Error.
 * Used for API failures. Includes a 'data' property to hold detailed server responses.
 * @extends AppError
 */
class BackendError extends AppError {

    /**
     * @param {Object} params - See AppError for details.
     * @param {Object} [params.data={}] - Raw JSON response from the server (e.g., Django field errors).
     */
    constructor({ message = 'Backend Error', color = 'red', time = 2000, field = '', data = {} } = {}) {
        super({ message, color, time, field });
        this.data = data;
        this.name = "BackendError";
    }
}


/**
 * Front-end Validation Error.
 * Used for client-side checks (empty fields, regex failure, business logic).
 * @extends AppError
 */
class ValidationError extends AppError {

    /**
     * @param {Object} params - See AppError for details.
     */
    constructor({ message = 'Validation Error', color = 'orange', time = 2500, field = '' } = {}) {
        super({ message, color, time, field });
        this.name = "ValidationError";
    }
}


/**
 * Standardizes raw validation result objects.
 * Useful for legacy code or utility functions that return objects instead of throwing.
 * 
 * * @param {Object} params - The error configuration object.
 * @param {boolean} [params.error=true] - Flag to indicate a failure.
 * @param {string} [params.field=''] - Input name related to the error.
 * @param {string} [params.message=''] - UI message.
 * @param {string} [params.color='red'] - Alert color.
 * @param {number} [params.time=1500] - Alert duration.
 * @returns {Object} A standardized map: { error, field, message, color, time }.
 */
function getErrorMapForm({ error = true, field = '', message = '', color = 'red', time = 2500 }) {
    return { error, field, message, color, time };
}
