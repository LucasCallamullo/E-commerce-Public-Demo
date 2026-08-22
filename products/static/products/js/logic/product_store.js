// export by CATALOG_MODAL_STORE    ; PRODUCT_MODAL_STORE

class CatalogStore {
    static #instance;

    constructor() {
        if (CatalogStore.#instance) {
            return CatalogStore.#instance;
        }
        this.categories = [];
        this.brands = [];
        CatalogStore.#instance = this;
    }

    static getInstance() {
        if (!CatalogStore.#instance) {
            CatalogStore.#instance = new CatalogStore();
        }
        return CatalogStore.#instance;
    }

    /**
     * Inicializa el catálogo con datos de marcas y categorías.
     * @param {Array} categories - Lista de categorías.
     * @param {Array} brands - Lista de marcas.
     */
    setCatalog(categories, brands) {
        this.categories = categories || [];
        this.brands = brands || [];
    }

    getCategories() {
        return this.categories;
    }

    getBrands() {
        return this.brands;
    }

    /**
     * Finds a category by its unique ID within the catalog.
     * * @param {number} id - The unique identifier of the category.
     * @returns {Object|null} The category object (including its metadata) or null if not found.
     */
    getCategoryById(id) {
        if (id === 0) return null;
        // Based on structure: { category: { id, name, slug } }
        return this.categories.find(c => c.category.id === id) || null;
    }

    /**
     * Finds a specific subcategory by its ID and its parent category ID.
     * * This method traverses the hierarchical category tree to locate a subcategory,
     * ensuring it belongs to the specified parent category for data integrity.
     * * @param {number} subcatId - The unique identifier of the subcategory.
     * @param {number} categoryId - The ID of the parent category.
     * @returns {Object|null} The subcategory object or null if no match is found.
     */
    getSubcategoryById(subcatId, categoryId) {
        // 1. First, locate the parent category
        const parentCategory = this.getCategoryById(categoryId);
        // { category: { id, name, ... }, subcategories: [ {id, name} ] } que vimos antes
        if (!parentCategory || !parentCategory.subcategories) return null;

        // 2. Search for the subcategory within that parent's subcategories list
        return parentCategory.subcategories.find(sub => sub.id === subcatId) || null;
    }

    /**
     * Retrieves a brand's metadata from the catalog by its ID.
     * * @param {number} id - The unique identifier of the brand.
     * @returns {Object|null} The brand object containing name, slug, and image, or null if not found.
     */
    getBrandById(id) {
        return this.brands.find(b => b.id === id) || null;
    }
}

const CATALOG_MODAL_STORE = new CatalogStore();




class ProductStore {
    static #instance;

    constructor() {
        if (ProductStore.#instance) {
            return ProductStore.#instance;
        }

        this.data = [];
        ProductStore.#instance = this;
    }

    /**
     * Returns the unique instance of the Store.
     * @returns {ProductStore} The singleton instance.
     */
    static getInstance() {
        if (!ProductStore.#instance) {
            ProductStore.#instance = new ProductStore();
        }
        return ProductStore.#instance;
    }

    /**
     * Sets the internal product data store.
     * @param {Array<Object>} newData - An array of product objects to be stored.
     */
    setData(newData) {
        this.data = newData;
    }

    /**
     * Returns the current product data.
     * @returns {Array<Object>} The array of stored product objects.
     */
    getData() {
        return this.data;
    }

    /**
     * Finds a product by its unique ID.
     * @param {number|string} id - The product ID to search for.
     * @returns {Object|null} The matched product object, or null if not found.
     */
    findById(id) {
        return this.data.find(p => p.id === id) || null;
    }

    // --- Price Logic ---

    /**
     * Calculates the minimum and maximum prices from the product list,
     * taking into account any applicable discounts (percentage).
     * @returns {{min: number, max: number}} An object containing the floor-rounded min and max prices.
     */
    getPriceRange() {
        if (!this.data.length) return { min: 0, max: 0 };

        let minPrice = Infinity;
        let maxPrice = -Infinity;

        for (const p of this.data) {
            const price = parseFloat(p.price_ars);
            const discount = p.discount_ars || 0;

            const finalPrice = discount > 0
                ? price - (price * (discount / 100))
                : price;

            if (finalPrice < minPrice) minPrice = finalPrice;
            if (finalPrice > maxPrice) maxPrice = finalPrice;
        }

        return {
            min: Math.floor(minPrice),
            max: Math.floor(maxPrice),
        };
    }

    // --- Filtering ---

    /**
     * Filters products based on a specific price range (after discounts).
     * @param {number} min - Minimum price threshold.
     * @param {number} max - Maximum price threshold.
     * @returns {Array<Object>} Filtered list of products.
     */
    filterByPrice(min, max) {
        return this.data.filter(p => {
            const finalPrice = p.discount_ars > 0 
                ? p.price_ars - (p.price_ars * (p.discount_ars / 100)) 
                : p.price_ars;
            return finalPrice >= min && finalPrice <= max;
        });
    }

    /**
     * Filters products by their Brand ID.
     * @param {number} brandId - The ID of the brand. Use 0 to return all products.
     * @returns {Array<Object>} Filtered list of products.
     */
    filterByBrand(brandId) {
        if (brandId === 0) return this.data;
        return this.data.filter(p => p.brand_id === brandId);
    }

    /**
     * Filters products based on a search query supporting multiple words.
     * Each word in the query must be present in the product name (case-insensitive).
     * @param {string} query - The search string.
     * @returns {Array<Object>} Filtered list of products.
     */
    filterByName(query) {
        if (!query) return this.data;
        const words = query.toLowerCase().split(/\s+/);
        return this.data.filter(p => {
            const name = p.name.toLowerCase();
            return words.every(word => name.includes(word));
        });
    }

    // --- Sorting ---

    /**
     * Sorts the product data by price.
     * @param {boolean} [desc=false] - If true, sorts in descending order. Defaults to ascending.
     * @returns {Array<Object>} A new array of products sorted by price.
     */
    orderByPrice(desc = false) {
        return [...this.data].sort((a, b) =>
            desc ? b.price_ars - a.price_ars : a.price_ars - b.price_ars
        );
    }

    /**
     * Sorts the product data by discount percentage in descending order.
     * Products without a discount are treated as 0.
     * @returns {Array<Object>} A new array of products sorted from highest to lowest discount.
     */
    orderByDiscount() {
        return [...this.data].sort((a, b) => {
            const aDiscount = a.discount_ars || 0;
            const bDiscount = b.discount_ars || 0;
            return bDiscount - aDiscount;
        });
    }

    /**
     * Sorts the product data alphabetically by name (A-Z).
     * @returns {Array<Object>} A new array of products sorted by name.
     */
    orderByName() {
        return [...this.data].sort((a, b) => a.name.localeCompare(b.name));
    }

    // --- Brands Logic ---

    /**
     * Retrieves unique brands that are currently present in the product list.
     * It cross-references product brand IDs with a master brand list.
     * @param {Array<Object>|null} [brands=null] - An optional list of brands to filter against. 
     * If null, it fetches brands from the CATALOG_MODAL_STORE.
     * @returns {Array<Object>} A sorted list of unique brand objects.
     */
    getUniqueBrands(brands = null) {
        // Ensure we have a list of brands to work with
        const availableBrands = brands || CATALOG_MODAL_STORE.getBrands();

        // Create a Set of brand IDs from current products for O(1) lookup performance
        const brandIdsSet = new Set(this.data.map(p => p.brand_id));
        
        // Filter the master list to include only brands that have products in 'this.data'
        const uniqueBrands = availableBrands.filter(brand => brandIdsSet.has(brand.id));
        
        // Return brands sorted alphabetically by name
        return uniqueBrands.sort((a, b) => a.name.localeCompare(b.name));
    }

}

const PRODUCT_MODAL_STORE = new ProductStore();
