from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from core.permissions import IsAdminOrSuperUser


from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import uuid
import os
from django.conf import settings


class GenericUploadImageAPIView(APIView):
    permission_classes = [IsAdminOrSuperUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        # 1. Validates that files were uploaded
        if not request.FILES:
            return Response({"detail": "No se enviaron archivos."}, status=status.HTTP_400_BAD_REQUEST)

        # lista de imagenes
        images = request.FILES.getlist('images')
        if not images:
            return Response({"detail": "El campo 'images' está vacío."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 1. Manejo seguro de booleanos (pueden venir como strings)
        multi = request.data.get('multiple')
        if isinstance(multi, str):
            multi = multi.lower() == 'true'
        else:
            multi = bool(multi)
            
        folder = request.data.get('folder', 'others') # 'products', 'banners', 'brands', etc.
        
        
        new_urls = []
        for img in images:
            # Aseguramos que el cursor esté al inicio
            img.seek(0)
            
            # 1. Generar nombre único y ruta
            ext = os.path.splitext(img.name)[1].lower()
            unique_name = f"{uuid.uuid4().hex[:13]}{ext}"
            
            # 2. Construir la ruta relativa: 'products/nombre.webp'
            relative_path = os.path.join(folder, unique_name)
            
            # 3. Guardar físicamente
            # default_storage detecta automáticamente si es local o AWS S3
            saved_path = default_storage.save(relative_path, ContentFile(img.read()))
            
            # 4. Generamos la URL inteligente según el entorno
            # Resultado (Local): Te devuelve /media/banners/archivo.webp.
            # Resultado (AWS): Te devuelve https://tu-bucket.s3.amazonaws.com/banners/archivo.webp?AWSA..
            full_url = default_storage.url(saved_path)
            
            new_urls.append(full_url)
        
            # para cortar a la primera ( esto es porque products puede usar 
            # más de una vez este endpoint )
            if not multi:
                break
            

        return Response({
            "success": True,
            # Si no es multi, devolvemos un string simple para no romper tu JS viejo
            # o la lista completa si es multi.
            "image_url": new_urls[0] if not multi else None,
            "images_urls": new_urls if multi else None
        })


"""
from core.utils.utils_image import get_url_from_imgbb

class GenericUploadImageAPIView(APIView):
    
    Generic endpoint to upload images to ImgBB.
    Returns the URL of the first uploaded image.
    
    Permissions:
        Only accessible by users with admin role or superuser (user.id == 1).
    
    Notes:
        - Only the first image of the uploaded list is processed.
        - Uses MultiPartParser for POST requests to handle file uploads.
        - Handles both known (ValueError) and unexpected exceptions gracefully.
    
    
    # Permission check for admin or superuser
    permission_classes = [IsAdminOrSuperUser]
    
    def get_parsers(self):
        
        Return parsers depending on the HTTP method.
        
        - POST: returns MultiPartParser to allow file uploads
        - GET, DELETE: uses default parsers from base class or DRF settings
        
        Returns:
            list: List of DRF parser classes for the current request
        
        # Si self.request no existe (como durante la generación del esquema),
        # retorna los parsers por defecto.
        if self.request is None or self.request.method == 'POST':
            return [MultiPartParser()]  # Parser to receive uploaded files
        return super().get_parsers()
    
    def post(self, request):
        
        Handles POST requests to upload images.
        
        Args:
            request (Request): DRF request object containing uploaded files
            
        Returns:
            Response: DRF Response with status and result information
        
        # 1. Validates that files were uploaded
        if not request.FILES:
            return Response({"detail": "No se enviaron archivos."}, status=status.HTTP_400_BAD_REQUEST)

        images = request.FILES.getlist('images')
        if not images:
            return Response({"detail": "El campo 'images' está vacío."}, status=status.HTTP_400_BAD_REQUEST)
            
        # 2. Processes only the first image to avoid unnecessary multiple uploads
        first_image = images[0]
        try:
            # Upload and validate image via ImgBB utility
            url = get_url_from_imgbb(first_image)
            
            # 3. Returns the image URL if successful
            return Response({"success": True, "image_url": url}, status=status.HTTP_201_CREATED)

        except ValueError as e:  # Known errors (unsupported format, etc.)
            return Response({"success": False, "detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:  # Unexpected errors
            # logger.error(f"Error uploading image: {str(e)}")  # Log the error
            return Response(
                {"success": False, "detail": "Error interno al procesar la imagen."}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
"""