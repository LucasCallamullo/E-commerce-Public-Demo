

// Variable global para detectar si estamos en vista móvil
let IS_MOBILE = window.innerWidth <= 992;

/**
 * Global registry for data injected from Django via json_script.
 * Acts as a single source of truth for the frontend application.
 * * Implementation: SINGLETON PATTERN
 */
class DjangoConfig {
    static #instance = null;

    /** * List of DOM IDs expected to contain JSON data from Django.
     * @type {string[]} 
     */
    static EXPECTED_KEYS = ['cart-data', 'store-data', 'auth-status', 'user-role'];

    /** * Centralized Icon Library (Remix Icon classes)
     * @type {Object<string, string>} 
     */
    static ICONS = {
        close: 'ri-close-circle-line',
        cross: 'ri-close-fill',
        default: 'ri-question-line',
        delete: 'ri-delete-bin-line',
        dot_desc: 'ri-git-commit-fill',
        edit: 'ri-edit-line',
        error: 'ri-close-circle-line',
        heart: 'ri-heart-fill',
        heartEmpty: 'ri-heart-line',
        info: 'ri-information-2-line',
        moon: 'ri-moon-line',
        success: 'ri-checkbox-circle-line',
        sun: 'ri-contrast-2-line',
        warning: 'ri-error-warning-line',
        wsp: 'ri-whatsapp-line'
    };

    /** * Semantic Color Palette.
     * Designed to work with CSS Variables defined in :root.
     * @type {Object<string, string>} 
     */
    static COLORS = {
        // var(nombre, fallback)
        blue: 'var(--color-info, #0000ff)',
        green: 'var(--color-success, #00c01a)',
        red: 'var(--color-error, #be0404e3)',
        yellow: 'var(--color-warning, #ffff00)',
        orange: 'var(--color-warning, #ffff00)',
        main: 'var(--main-color, #5e08e7)',
        main_light: 'var(--main-light-color, #9554ff)'
    };

    /** * Maps semantic colors to their logical alert status.
     * @type {Object<string, string>} 
     */
    static ICONS_ALERT_BY_COLOR = {
        green: 'success',
        red: 'error',
        blue: 'info',
        yellow: 'warning',
        orange: 'warning',
        default: 'success'
    };

    /** @type {boolean} Global debug flag */
    static DEBUG = false;

    constructor() {
        // SINGLETON PATTERN
        if (DjangoConfig.#instance) return DjangoConfig.#instance;

        /** @private @type {Map<string, any>} Internal store for parsed JSON data. */
        this._cache = new Map();
        
        /** @private @type {boolean} Tracks viewport size state. */
        this._isMobile = window.innerWidth <= 992;

        this._setupResizeListener();
        this._initialize();

        DjangoConfig.#instance = this;
    }

    /**
     * Retrieves the CSS class for an icon by its semantic name.
     * If the requested name does not exist, it returns a default fallback icon.
     * @param {keyof DjangoConfig.ICONS} name - Semantic key (e.g., 'edit').
     * @returns {string} Remix Icon CSS class.
     */
    getIcon(name) {
        const { ICONS } = DjangoConfig;
        return ICONS[name] || ICONS['default'];
    }

    /**
     * Maps a semantic color key to its corresponding status icon.
     * This creates a bridge between the color palette and the icon set.
     * @param {keyof DjangoConfig.ICONS_ALERT_BY_COLOR} color - Semantic color (e.g., 'green').
     * @returns {string} CSS class of the matched status icon.
     */
    getIconByColor(color) {
        const mapping = DjangoConfig.ICONS_ALERT_BY_COLOR;
        const iconKey = mapping[color] || 'default';
        return this.getIcon(iconKey);
    }

    /**
     * Retrieves a CSS color variable or a fallback hex code.
     * Designed to work seamlessly with CSS Variables defined in the :root.
     * @param {keyof DjangoConfig.COLORS} key - Semantic color name.
     * @returns {string} A CSS 'var()' declaration or a hex color code.
     */
    getColor(key) {
        const { COLORS } = DjangoConfig;
        return COLORS[key] || COLORS.green;
    }

    /**
     * Retrieves the complete store configuration object.
     * @returns {Object|null} The store data object or null if not loaded.
     */
    getStore() {
        return this._cache.get('store-data') || null;
    }

    /**
     * Retrieves the store's operating schedules.
     * @returns {string} The schedules string or an empty string if not available.
     */
    getStoreSchedules() {
        // Uses optional chaining to safely access the schedules property
        return this.getStore()?.schedules || '';
    }

    /**
     * Retrieves the store's description.
     * If a formal description is missing, it falls back to a formatted 
     * version of the store's name or an empty string.
     * @returns {string} The store description or fallback name.
     */
    getStoreDescription() {
        const store = this.getStore();
        
        // Logical OR chain: 
        // 1. Try formal description
        // 2. Fallback to name formatted as a Markdown header
        // 3. Absolute fallback to empty string
        return store?.description || (store?.name ? `## ${store.name}` : '');
    }

    /**
     * Retrieves the store's primary contact number.
     * Logic: Prioritizes 'wsp_number' for WhatsApp actions, 
     * falls back to 'cellphone', and defaults to an empty string.
     * @returns {string} The formatted or raw contact number.
     */
    getStoreCellphone() {
        const store = this.getStore();
        // Uses optional chaining to safely access nested properties
        return store?.wsp_number || store?.cellphone || '';
    }
    
    /**
     * Checks if the current user has administrative privileges.
     * @returns {boolean} True if the user role is 'admin'.
     */
    get isAdmin() {
        const role = this._cache.get('user-role');
        return role === 'admin';
    }

    /**
     * Checks if the user is currently authenticated.
     * @returns {boolean} True if the user is authenticated.
     */
    get isAuthenticated() {
        return this.get('auth-status') === true;
    }

    /** @returns {boolean} */
    get DEBUG() {
        return (this.constructor.DEBUG);
    }

    /**
     * Retrieves data by key.
     * @param {'cart-data' | 'store-data' | 'auth-status' | 'user-role'} key
     * @returns {any} The parsed data or null if not found.
     */
    get(key) {
        return this._cache.get(key) || null;
    }

    /**
     * Getter to check if the current viewport is mobile-sized.
     * @returns {boolean}
     */
    get isMobile() {
        return this._isMobile;
    }

    /**
     * Initializes a debounced listener to update the mobile state
     * only after the user has finished resizing the window.
     * @private
     */
    _setupResizeListener() {
        // Assuming 'debounce' is a globally available utility
        const handleResize = debounce(() => {
            this._isMobile = window.innerWidth <= 992;
            if (DjangoConfig.DEBUG) {
                console.log(`[DjangoConfig]: Viewport updated. isMobile: ${this._isMobile}`);
            }
        }, 250);    // 250ms is enough for a smooth feel

        window.addEventListener("resize", handleResize);
    }

    /** * Parses JSON data from the DOM based on EXPECTED_KEYS.
     * @private 
     */
    _initialize() {
        // Accessing static EXPECTED_KEYS via constructor
        DjangoConfig.EXPECTED_KEYS.forEach(id => {
            const element = document.getElementById(id);
            if (element) {
                try {
                    this._cache.set(id, JSON.parse(element.textContent));
                } catch (err) {
                    if (DjangoConfig.DEBUG) {
                        logger(`[DjangoConfig]: Error parsing JSON for #${id}`, 'red');
                        console.error(`[DjangoConfig]: Error parsing JSON for #${id}`, err);
                    }
                    this._cache.set(id, null);
                }
            }
        });
    }

    /** Static entry point for the Singleton instance */
    static getInstance() {
        if (!this.#instance) this.#instance = new DjangoConfig();
        return this.#instance;
    }
}

// Global instance
const APP_CONFIG = new DjangoConfig();
