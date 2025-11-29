


from django.conf import settings
from django.core.management.base import BaseCommand


# from scripts.database_fixes.fix_main_image import update_fix_main_image
from products.data.load_store import load_store_init

from products.models import Product
from home.models import Store, StoreImage
from products import filters


class Command(BaseCommand):
    help = "Es un comando exclusivamente para ejecutar algunos scripts que no se podian ejecutar en railway"
    
    def handle(self, *args, **kwargs):
        # update_fix_main_image()
        # load_store_init()
        # update_new_store_image_model()
        update_some_orders()
        
        
def update_some_orders():
    from orders.models import Order, ItemOrder
    from decimal import Decimal
    
    orders = Order.objects.all()
    discount_coupon = Decimal("2.00")
    
    for order in orders:
        
        if order.total == 0:
            # Actualizar la orden con estos campos
            price_shipment = order.shipment.method.price
            order.shipment_cost = price_shipment
            order.discount_coupon = discount_coupon
            
            subtotal = 0
            items = ItemOrder.objects.filter(order=order)
            for item in items:
                subtotal += (item.quantity * item.final_price)
                
            order.total = subtotal + price_shipment - discount_coupon
            order.save(update_fields=["shipment_cost", "discount_coupon", "total"])
            print(f'actualizado: {order.id}')
        
        
def update_new_store_image_model():
    # agregar headers imagenes al ecommerce iniciales
    list_headers = [
        "https://redragon.es/content/uploads/2021/10/HEROS-S129W-BA.jpg",
        "https://sigmatiendas.com/cdn/shop/files/Logitech_banner_product_page_v2.jpg?v=1711139345&width=2800",
        "https://assets2.razerzone.com/images/pnx.assets/4b93db266e7ee65c3a25a5ae582ed586/razer-affiliate-hero-mobile.jpg"
    ]
 
    
    store = Store.objects.get(id=1)
    
    flag = True
    for header in list_headers:
        imagen, create = StoreImage.objects.get_or_create(
            store=store, image_url=header, main_image=flag, available=True, image_type='header'
        )
        if create:
            flag = False
            print(f"se agrego el header_image con {imagen.image_url}")
    
    
    list_banners = [
        "https://www.techgames.com.mx/wp-content/uploads/2021/10/Logitech-G-y-Riot-Games-LOL.jpg",
        "https://redragonshop.com/cdn/shop/files/referal-candy-banner-m.png?v=1709540400"
    ]
    
    flag = True
    for header in list_banners:
        imagen, create = StoreImage.objects.get_or_create(
            store=store, image_url=header, main_image=flag, available=True, image_type='banner'
        )
        if create:
            flag = False
            print(f"se agrego el header_image con {imagen.image_url}")
    

    
    
def updates_main_image_field():
    products = Product.objects.all()
    
    for product in products:
        # product.update_main_image_url()    # ya no existe esta funcion no de la misma forma OJO
        print(f"name: {product.name} | main image: {product.main_image}")
        # product.save()
        
    # Usar bulk_update para actualizar todos los productos en una sola consulta
    # Product.objects.bulk_update(products, ['main_image'])
        
        
def updates_normalized_names():
    """
    Usar bulk_update es una forma más eficiente de actualizar varios objetos sin llamar a save() 
    en cada uno de ellos, especialmente cuando necesitas actualizar el mismo campo para muchos 
    registros.
    """
    
    products = Product.objects.all()
        
    for product in products:
        product.normalized_name = filters.normalize_or_None(product.name)
        print(f"name: {product.name} | normalized_name: {product.normalized_name}")
        
    # Usar bulk_update para actualizar todos los productos en una sola consulta
    Product.objects.bulk_update(products, ['normalized_name'])