from products.services.category import CategoryService

def get_categories_n_subcats(request):
    # Tries to get the data from the cache to optimize performance by querying only once
    # instead of doing it every time
    return {
        'categories_dropmenu': CategoryService.get_categories_list()
    }