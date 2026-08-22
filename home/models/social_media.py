from django.db import models


class SocialMedia(models.Model):
    """
    Manages social media profiles associated with a Store.
    
    Includes a platform mapping to Remix Icon classes for frontend rendering.
    Enforces a unique platform per store via Meta constraints.
    """
    
    class PlatformEnum(models.TextChoices):
        """Enumeration of supported social media platforms."""
        FB = 'fb', 'Facebook'
        GG = 'gg', 'Google'
        GM = 'gm', 'Google Maps'
        IG = 'ig', 'Instagram'
        TT = 'tt', 'TikTok'
        TW = 'tw', 'X (Twitter)'
        YT = 'yt', 'YouTube'
    
    store = models.ForeignKey('home.Store', related_name='social_networks', on_delete=models.CASCADE)
    platform = models.CharField(
        max_length=10, 
        choices=PlatformEnum.choices, 
        default=PlatformEnum.IG
    )
    url = models.URLField(blank=True, null=True, default="https://www.instagram.com")
    is_active = models.BooleanField(default=True)
    is_main = models.BooleanField(default=False)

    class Meta:
        unique_together = ('store', 'platform')
        
    def __str__(self):
        return f"{self.get_platform_display()} - {self.store.name}"
        
    @staticmethod
    def get_icon_class(value: str) -> str:
        """
        Returns the specific Remix Icon (ri-) class based on the platform.
        Usage in templates: {{ object.icon_class }}
        """
        icons = {
            'gg': 'ri-google-fill',
            'ig': 'ri-instagram-line',
            'fb': 'ri-facebook-box-fill',
            'tt': 'ri-tiktok-fill',
            # 'tw': 'ri-twitter-line',
            'tw': 'ri-twitter-x-line',
            'yt': 'ri-youtube-fill',
            'gm': 'ri-pin-distance-line',
        }
        # Returns a generic community icon if the platform is not found
        return icons.get(value, 'ri-user-community-line') # Icono por defecto
