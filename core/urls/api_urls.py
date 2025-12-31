from django.urls import path
from core.views.upload_images import GenericUploadImageAPIView

urlpatterns = [
    # generic endpoint to upload images for any model except Product
    path('api/upload/image', GenericUploadImageAPIView.as_view(), name='upload-images-api'),
]