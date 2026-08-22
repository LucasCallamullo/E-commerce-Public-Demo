/// <reference path="../js/app_config.js" />
/// <reference path="../js/base.js" />
/// <reference path="../js/alerts.js" />


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
 * Initializes and renders store-related information in the footer.
 * * This function fetches raw Markdown data for descriptions and schedules 
 * from the centralized configuration, translates them into HTML, and 
 * updates all corresponding DOM elements found on the page.
 * * @function initFooterDescriptions
 */
function initFooterDescriptions() {

    // 1. Process Store Descriptions
    // Selects all elements intended to display the store's "about" or description text.
    const spans = document.querySelectorAll('.store-description');
    const md_desc = APP_CONFIG.getStoreDescription();
    const description = translateCustomMarkdown(md_desc);
    
    // Batch update all description containers
    spans.forEach(p => p.innerHTML = description );
    
    // 2. Process Store Schedules
    // Selects all elements intended to display operating hours.
    const spanss = document.querySelectorAll('.store-schedules');
    const md_ss = APP_CONFIG.getStoreSchedules();
    const schedules = translateCustomMarkdown(md_ss);
    
    // Batch update all schedule containers
    spanss.forEach(p => p.innerHTML = schedules );
}


/**
 * Custom Markdown to HTML Translator.
 * Processes a restricted subset of Markdown and custom shortcodes (YouTube)
 * into semantic HTML strings.
 * * Supported Syntax:
 * - Titles: "## Title" -> <h3>
 * - Line Breaks: "--" -> <br>
 * - YouTube: "YT[url/id]" -> Responsive iframe
 * - Bold: "**text**" -> <b> (styled)
 * - Highlights: "(*)" -> Styled bold indicator
 * - Custom Bullets: "* " -> Icon, "*- " -> Unicode bullet
 * - Links: "[text](url)" -> <a> (external)
 * * @param {string} text - The raw markdown-like text to translate.
 * @returns {string} The resulting HTML string.
 */
function translateCustomMarkdown(text) {
    // Splits by line, trims whitespace, and ignores empty strings
    const lines = text.split('\n').map(line => line.trim()).filter(line => line);

    const dot_desc = APP_CONFIG.getIcon('dot_desc');

    const htmlLines = lines.map(line => {
        // --- 1. ELEMENTOS DE BLOQUE (Línea completa) ---
        
        // Títulos: Detecta "## " al inicio. Retorna un <h3> y detiene el procesamiento de esa línea.
        if (/^##\s+/.test(line)) {
            const titleText = line.replace(/^##\s+/, '');
            return /*html*/`<h3 class="font-lg">${titleText}</h3>`;
        }

        // Separador / Salto: Si la línea es exactamente "--", inserta un <br>.
        if (line === '--') return /*html*/`<br>`;

        // Video de YouTube: Si la línea contiene YT[codigo], genera el iframe.
        // Se procesa antes que el <p> para evitar anidación incorrecta.
        if (/YT\[(.+?)\]/.test(line)) {
            const rawContent = line.match(/YT\[(.+?)\]/)[1];

            // Esta Regex busca el ID de 11 caracteres en cualquier formato de URL de YouTube
            const videoIdMatch = rawContent.match(
                /(?:youtu\.be\/|youtube\.com\/(?:.*v=|\/embed\/|v\/))?([a-zA-Z0-9_-]{11})/
            );
            const cleanId = videoIdMatch ? videoIdMatch[1] : rawContent;
            
            return /*html*/`
                <div class="video-container my-2">
                    <iframe 
                        width="100%" height="315"    
                        src="https://www.youtube.com/embed/${cleanId}"
                        title="YouTube video player" 
                        frameborder="0" 
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; 
                        gyroscope; picture-in-picture; web-share" 
                        referrerpolicy="strict-origin-when-cross-origin"
                        allowfullscreen>
                    </iframe>
                </div>`;
        }

        // --- 2. ELEMENTOS INLINE (Dentro del texto) ---

        // Notación especial (*): Resalta el símbolo asterisco entre paréntesis.
        line = line.replace(/\(\*\)/g, /*html*/`<b>(*)</b>`); 

        // Negritas: Transforma **texto** en etiquetas <b> con clase específica.
        line = line.replace(/\*\*(.+?)\*\*/g, /*html*/`<b class="font-md">$1</b>`);

        // Bullets (Puntos): Reemplaza el "*" al inicio por un icono o el "*-" por un punto simple.
        if (/^\*\s+/.test(line)) {
            line = line.replace(/^\*\s+/, /*html*/`<i class="${dot_desc} font-md"></i>`); 
        } else if (/^\*-\s+/.test(line)) {
            line = line.replace(/^\*-\s+/, '• ');
        }

        // Enlaces: Formato [texto](url).
        line = line.replace(
            /\[(.+?)\]\((.+?)\)/g, 
            /*html*/`<a href="$2" target="_blank" class="bold-main-light fw-normal-plus">$1</a>`
        );

        // Wrap any remaining plain text in paragraph tags
        return /*html*/`<p>${line}</p>`;
    });

    return htmlLines.join('');
}


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


/**
 * Utility to safely retrieve JSON data from Django json_script tags.
 * @param {string} id - The ID assigned in the template.
 * 
 * @returns {Object|null}
 */
const getDjangoData = (id, debug = false) => {
    // 1. Get the raw JSON string from the script tag
    const el = document.getElementById(id);

    // 2. Parse it into a JS Object
    const data = el ? JSON.parse(el.textContent) : null;

    if (debug) {
        // 3. Optional: Verify in console
        console.log(`Data from ${id}:`, data);
    }

    return data;
};


/**
 * Dark Mode Event Listener.
 * 
 */
/**
 * Theme Manager Module
 * Handles light/dark mode switching and persistence.
 */
function initThemeManager() {
    const htmlElement = document.documentElement;
    const themeToggleButtons = document.querySelectorAll('.theme-toggle');
    const themeIcons = document.querySelectorAll('.theme-icon');

    /**
     * Updates the UI icons based on the current theme.
     * Uses APP_CONFIG to retrieve centralized icon classes.
     * @param {'light'|'dark'} theme 
     */
    function updateThemeIcons(theme) {
        const isDark = theme === 'dark';
        themeIcons.forEach(icon => {
            // Usamos nombres semánticos de tu CONFIG
            icon.classList.toggle(APP_CONFIG.getIcon('moon'), !isDark);
            icon.classList.toggle(APP_CONFIG.getIcon('sun'), isDark);
            // icon.className = `theme-icon ${isDark ? APP_CONFIG.getIcon('sun') : APP_CONFIG.getIcon('moon')}`;
        });
    }

    /**
     * Applies the theme to the document and saves preference.
     * @param {'light'|'dark'} theme 
     */
    function setTheme(theme) {
        // limpiar clases
        htmlElement.classList.remove('light-mode', 'dark-mode');

        htmlElement.classList.add(`${theme}-mode`);
        localStorage.setItem('themePreference', theme);
        updateThemeIcons(theme);
    }

    /**
     * Cycles between light and dark themes.
     */
    function cycleTheme() {
        const nextTheme = htmlElement.classList.contains('dark-mode') ? 'light' : 'dark';
        setTheme(nextTheme);
    }

    // Event Listeners
    themeToggleButtons.forEach(btn => btn.addEventListener('click', cycleTheme));

    // Initialization: Priority 1. LocalStorage | 2. Default Light
    // Only update if we're in auto mode
    const savedTheme = localStorage.getItem('themePreference') || 'light';
    setTheme(savedTheme);
}


/**
 * Custom logger that prints a message and optional data followed by a separator.
 * Only executes if debug mode is enabled.
 * * @param {string} msg - The main message to display.
 * @param {any[]} params - Optional objects, arrays, or variables to inspect.
 */
function logger(msg, color = 'blue', time = 1000, ...params) {
    // stupid check
    if (!APP_CONFIG.DEBUG) return;

    const separator = "%c=========================================";
    const styles = [
        "color: #5e08e7; font-weight: bold;", // Violeta principal
        "color: #9554ff; font-weight: bold;", // Lila claro
        "color: #008b8b; font-weight: bold;", // Verde agua oscuro (DarkCyan)
        "color: #228b22; font-weight: bold;", // Verde bosque (ForestGreen)
        "color: #c71585; font-weight: bold;"  // Rosa oscuro (MediumVioletRed)
    ];
    // Elegimos un índice al azar entre 0 y el largo de la lista
    const randomIndex = Math.floor(Math.random() * styles.length);
    const selectedStyle = styles[randomIndex];
    
    console.log(msg);
    openAlert(msg, color, time);

    // If there are extra parameters, log them properly
    if (params.length > 0) {
        params.forEach(param => {
            // Si es un objeto, usa console.dir para poder desplegarlo; si no, log normal
            if (typeof param === 'object' && param !== null) {
                console.dir(param);
            } else {
                console.log(param);
            }
        });
    }

    console.log(separator, selectedStyle);
}


/**
 * Analyzes the current DOM structure and payload size.
 * * This function measures:
 * 1. Total DOM nodes (recursive count).
 * 2. HTML size in Bytes, KB, and MB.
 * 3. Performance impact (via console.time).
 * 4. Elements with excessive children (Threshold: 50).
 * * It runs recursively every 3 seconds for real-time monitoring.
 * 
 * * Analyzes the DOM but only for a limited number of iterations.
 * @param {number} iterations - How many times it should run.
 * 
 * @function analyzeHTML
 */
function analyzeHTML(iterations = 3) {
    // Si ya no quedan vueltas, nos detenemos
    if (iterations <= 0) {
        console.log("%cAnálisis automático finalizado.", "color: #ff9900; font-weight: bold;");
        return;
    }
    
    console.log("%c=========================================", "color: #5e08e7; font-weight: bold;");
    console.log(`Vuelta restante: ${iterations}`);
    console.time("Analysis Time");

    // 1. Recursive DOM Node Counter
    let totalNodes = 0;
    (function count(node) {
        totalNodes++;
        node = node.firstChild;
        while (node) {
            count(node);
            node = node.nextSibling;
        }
    })(document.documentElement);

    console.log(`Total DOM Nodes: ${totalNodes}`);

    // 2. HTML Payload Size Estimation
    const html = document.documentElement.innerHTML;
    const bytes = new Blob([html]).size;
    const kb = (bytes / 1024).toFixed(2);
    const mb = (kb / 1024).toFixed(2);

    // Tamaño aproximado del HTML
    console.log(`Tamaño del HTML:`);
    console.log(`→ Bytes: ${bytes}`);
    console.log(`→ KB: ${kb}`);
    console.log(`→ MB: ${mb}`);

    /* / 3. Identify Bloated Elements (Elements with > 50 children)
    const elementsWithManyChildren = [...document.querySelectorAll("*")]
        .map(el => ({ tag: el.tagName, count: el.children.length, el }))
        .filter(item => item.count > 50)
        .sort((a, b) => b.count - a.count);

    if (elementsWithManyChildren.length > 0) {
        console.warn(`High Density Elements (More than 50 children):`);
        elementsWithManyChildren.forEach(({ tag, count, el }) => {
            console.log(`→ <${tag}> with ${count} children:`, el);
        });
    } else {
        console.log("No bloated elements found (under 50 children).");
    } */

    console.timeEnd("Analysis Time");

    // Recursive call every 3 seconds for 3 times
    setTimeout(() => {
        analyzeHTML(iterations - 1);
    }, 3000);
}


/**
 * Forces a full page reload by appending or updating a unique query parameter to the current URL.
 *
 * This technique helps to bypass browser cache by ensuring the URL is unique on each reload.
 *
 * Usage:
 * You can place this function at the end of your JS file or inside a <script> tag
 * after the page has loaded.
 */
function forceReload() {
    const url = new URL(window.location.href);
    url.searchParams.set('v', Date.now()); // Add unique parameter to bust cache
    window.location.href = url.toString();
};
