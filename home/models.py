from django.db import models

# Create your models here.
class Store(models.Model):
    name = models.CharField(max_length=100)
    logo = models.URLField(blank=True, null=True)
    logo_wsp = models.URLField(blank=True, null=True)

    ig_url = models.URLField(blank=True, null=True, default="https://www.instagram.com")
    tw_url = models.URLField(blank=True, null=True, default="https://x.com/home")
    fb_url = models.URLField(blank=True, null=True, default="https://www.facebook.com")
    tt_url = models.URLField(blank=True, null=True, default="https://www.tiktok.com")
    
    google_url = models.URLField(blank=True, null=True)
    wsp_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=180, blank=True, null=True)
    cellphone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
    # datos especifico de la tienda
    bank = models.CharField(max_length=30, blank=True, null=True)
    name_cuit = models.CharField(max_length=50, blank=True, null=True)
    cuit = models.CharField(max_length=30, blank=True, null=True)
    cvu = models.CharField(max_length=30, blank=True, null=True)
    cbu = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name


class StoreImage(models.Model):
    IMAGE_TYPE = [
        ('header', 'Header'),
        ('banner', 'Banner'),
    ]
    
    store = models.ForeignKey('Store', related_name='images', on_delete=models.CASCADE)
    image_type = models.CharField(max_length=10, choices=IMAGE_TYPE, default='header')
    image_url = models.URLField(blank=True, null=True)
    main_image = models.BooleanField(default=False)
    available = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.image_type.capitalize()} Image {self.id} (main: {self.main_image})"

    class Meta:
        indexes = [
            models.Index(fields=['image_type', 'available', '-main_image']),
        ]
