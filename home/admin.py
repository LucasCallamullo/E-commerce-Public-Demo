from django.contrib import admin

# Register your models here.
from .models import Store, StoreImage


@admin.register(StoreImage)
class HeaderImagesAdmin(admin.ModelAdmin):
    list_display = ('id', 'main_image', 'available', 'image_url')
    list_filter = ('main_image',)
    actions = ['set_as_main_header']

    def set_as_main_header(self, request, queryset):
        StoreImage.objects.update(main_image=False)
        queryset.update(main_image=True)
    set_as_main_header.short_description = "Set selected as main header"


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'logo')
    list_filter = ('name',)

    def has_add_permission(self, request):
        # Permitir agregar solo si no existe ningún modelo Ecommerce
        if Store.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        # Evitar eliminar si es el único modelo Ecommerce
        if Store.objects.count() == 1:
            return False
        return super().has_delete_permission(request, obj)