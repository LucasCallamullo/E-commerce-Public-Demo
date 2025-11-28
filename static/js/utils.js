/// <reference path="../js/base.js" />
/// <reference path="../js/alerts.js" />


function analizarHTML() {
    console.time("⏱️ Tiempo de análisis");

    // Contar nodos del DOM
    let totalNodos = 0;
    (function contar(node) {
        totalNodos++;
        node = node.firstChild;
        while (node) {
            contar(node);
            node = node.nextSibling;
        }
    })(document.documentElement);

    console.log(`🧱 Total de nodos en el DOM: ${totalNodos}`);

    // Tamaño aproximado del HTML
    const html = document.documentElement.innerHTML;
    const bytes = new Blob([html]).size;
    const kb = (bytes / 1024).toFixed(2);
    const mb = (bytes / (1024 * 1024)).toFixed(2);

    console.log(`📄 Tamaño del HTML:`);
    console.log(`→ Bytes: ${bytes}`);
    console.log(`→ KB: ${kb}`);
    console.log(`→ MB: ${mb}`);
}
// Elementos con muchos hijos
/*
    const elementosConMuchosHijos = [...document.querySelectorAll("*")]
        .map(el => ({ tag: el.tagName, count: el.children.length, el }))
        .filter(item => item.count > 50)
        .sort((a, b) => b.count - a.count);

    if (elementosConMuchosHijos.length > 0) {
        console.log(`🔎 Elementos con muchos hijos (más de 50):`);
        elementosConMuchosHijos.forEach(({ tag, count, el }) => {
            console.log(`→ <${tag}> con ${count} hijos`, el);
        });
    } else {
        console.log("✅ No se encontraron elementos con más de 50 hijos.");
    }

    console.timeEnd("⏱️ Tiempo de análisis");
*/


function escapeHTML(str) {
    if (typeof str !== 'string') return str;
    return str
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function deepEscape(obj) {
    if (typeof obj === 'string') return escapeHTML(obj);
    if (Array.isArray(obj)) return obj.map(deepEscape);
    if (typeof obj === 'object' && obj !== null) {
        const escaped = {};
        for (const key in obj) {
            escaped[key] = deepEscape(obj[key]);
        }
        return escaped;
    }
    return obj;
}


/**
 * Formats a date string into a short Spanish date format: "D mmm. YYYY".
 *
 * Example:
 *   shortDate("2025-08-09T10:15:00") -> "9 ago. 2025"
 *
 * - Uses abbreviated month names in Spanish (ene., feb., mar., etc.).
 * - Returns an empty string if the input is null, undefined, or invalid.
 *
 * @param {string} dateStr - A date string that can be parsed by the Date constructor.
 * @returns {string} A formatted date in short Spanish format, or an empty string if invalid.
 */
function shortDate(dateStr) {
    const MONTHS_ABBR = {
        0: "ene.",
        1: "feb.",
        2: "mar.",
        3: "abr.",
        4: "may.",
        5: "jun.",
        6: "jul.",
        7: "ago.",
        8: "sep.",
        9: "oct.",
        10: "nov.",
        11: "dic."
    };

    if (!dateStr) return '';
    const date = new Date(dateStr);
    if (isNaN(date)) return ''; // Handle invalid date

    const day = date.getDate();
    const month = MONTHS_ABBR[date.getMonth()];
    const year = date.getFullYear();

    return `${day} ${month} ${year}`;
}



/**
 * Debounce utility
 * 
 * Retrasa la ejecución de una función hasta que haya pasado un tiempo determinado 
 * desde la última vez que se invocó.
 * 
 * @param {Function} func - Función a ejecutar después del retraso.
 * @param {number} wait - Tiempo en milisegundos a esperar.
 * @returns {Function} - Nueva función con comportamiento de debounce.
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout); // Resetea el temporizador si la función es llamada de nuevo
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}


// Variable global para detectar si estamos en vista móvil
let IS_MOBILE = window.innerWidth <= 992;
window.addEventListener("resize", () => {
    // Función que actualiza el estado de `isMobile`
    function checkIsMobile() {
        IS_MOBILE = window.innerWidth <= 992;
    }
    debounce(checkIsMobile, 500);
});



/**
 * Formats a number by adding dots as thousand separators.
 * 
 * @param {number|string} number - The number to be formatted (can be an integer, float, or string).
 * @param {bool} allowZero - This flag allow returns Zero for some case.
 * @returns {string} The formatted number as a string with dots as thousand separators.
 */
function formatNumberWithPoints(number, allowZero = false) {
    // If the value is null, undefined, or an empty string, return a blank space
    if (number === null || number === undefined || number === "") return " ";

    // Convert the string value to a number
    const price = parseFloat(number);
    
    // Check if the price is 0
    if (price === 0) 
        if (!allowZero) return 'Gratis';
        else return price;

    // If the number is an integer, format it with thousand separators using dots
    if (Number.isInteger(price)) return price.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".");

    // If the number has decimals, format it by separating thousands with dots and decimals with a comma
    let [integerPart, decimalPart] = price.toString().split(".");
    integerPart = integerPart.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    
    return decimalPart ? `${integerPart},${decimalPart}` : integerPart;
}





/**
 * Dark Mode Event Listener.
 * 
 */
document.addEventListener('DOMContentLoaded', () => {
    const themeToggleButtons = document.querySelectorAll('.theme-toggle');
    const themeIcons = document.querySelectorAll('.theme-icon');
    const htmlElement = document.documentElement;

    function setTheme(theme) {
        // Limpia todas las clases primero
        htmlElement.classList.remove('light-mode', 'dark-mode');
        
        if (theme === 'light') {
            htmlElement.classList.add('light-mode');
            localStorage.setItem('themePreference', 'light');
        } else if (theme === 'dark') {
            htmlElement.classList.add('dark-mode');
            localStorage.setItem('themePreference', 'dark');
        }
        
        updateThemeIcons(theme);
    }

    function updateThemeIcons(theme) {
        const isDark = theme === 'dark';
        
        themeIcons.forEach(icon => {
            icon.classList.toggle('ri-moon-line', !isDark);
            icon.classList.toggle('ri-contrast-2-line', isDark);
        });
    }

    function cycleTheme() {
        const currentTheme = htmlElement.classList.contains('dark-mode') ? 'dark' : 'light';
        const nextTheme = currentTheme === 'light' ? 'dark' : 'light';
        setTheme(nextTheme);
    }
    
    themeToggleButtons.forEach(button => {
        button.addEventListener('click', cycleTheme);
    });

    // Only update if we're in auto mode
    if (!localStorage.getItem('themePreference')) {
        // Inicializa con el tema claro por defecto (ignorando localStorage)
        setTheme('light');
    } else {
        const currentPreference = localStorage.getItem('themePreference') || 'light';
        setTheme(currentPreference);
    }
});


/**
 * Retrieves the value of a specified cookie by its name, commonly used for CSRF tokens.
 * 
 * @param {string} name - The name of the cookie whose value is to be retrieved.
 * @returns {string|null} The value of the cookie if found, otherwise null.
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Checks if the cookie has the desired name
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                // Extracts and decodes the cookie value
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
