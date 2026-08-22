
# test_delete_images_files.py
# pytest home -s --log-cli-level=DEBUG
# pytest home/tests/test_delete_images_files.py -s --log-cli-level=DEBUG
# pytest home/tests/test_delete_images_files.py -xvs --reuse-db --tb=short --log-cli-level=DEBUG


# docker-compose exec web_client_1 pytest home/tests/test_delete_images_files.py -s
import pytest
from unittest.mock import patch
from django.db import transaction
from home.models.store_images import StoreImage


# I use transactional=True to test transaction.on_commit hooks.
# 'available_apps' is critical here: PostgreSQL prevents TRUNCATE on tables 
# referenced by Foreign Keys (like ProductImage -> Product). By limiting 
# available_apps, we exclude those complex relations from the test's 
# database cleanup phase, avoiding "FeatureNotSupported" errors.
@pytest.mark.django_db(transaction=True, available_apps=[
    'home', 
    'django.contrib.auth', 
    'django.contrib.contenttypes'
])
class TestDeleteStoreImages:
    TARGET_MOCK = 'home.signals.storage_signals.delete_physical_files_from_urls'

    @pytest.fixture
    def other_image(self, store_data):
        image = StoreImage.objects.create(
            store=store_data,
            image_type=StoreImage.ImageType.HEADER,
            image_url='https://example.com/second.jpg',
            main_image=False,
            available=True
        )
        print("=" * 50)
        return image
    
    
    def test_transactional_queue_order(self, initial_image, other_image):
        """
        Validates that on_commit hooks are queued and only executed 
        after the outer atomic block finishes successfully.
        """
        with patch(self.TARGET_MOCK) as mock_delete:
            old_url = initial_image.image_url
            
            with transaction.atomic():
                # ==========================================================
                # Task 1: URL Change (Should queue a deletion)
                # ==========================================================
                new_url = 'https://example.com/media/realmente_cambio.jpg'

                # Pre-signal check
                assert initial_image._original_url == old_url
                
                initial_image.image_url = new_url
                initial_image.save(update_fields=['image_url'])
                
                # Hook is registered but NOT executed yet because we are inside the transaction
                mock_delete.assert_not_called()
                
                # Post-signal: _original_url should be updated to match the new URL
                assert initial_image._original_url == new_url
                
                # ==========================================================
                # Task 2: Field Update (Should NOT queue anything)
                # ==========================================================
                other_url = other_image.image_url
                other_image.main_image = False
                
                # Pre-signal check
                assert other_image._original_url == other_url
                
                # Act: Save a different field
                other_image.save(update_fields=['main_image'])
                
                # Still no execution
                mock_delete.assert_not_called()
                
                # Post-signal: URL remains the same, so _original_url shouldn't change
                assert other_image._original_url == other_url
                
                # Integrity checks
                other_image.refresh_from_db()
                assert other_image.image_url == other_url
                
                # Database state is updated in the current transaction session
                initial_image.refresh_from_db()
                assert initial_image.image_url == new_url
                
                # ==========================================================
                # Task 3: Field Update INITIAL_IMAGE again for check safety calls
                # ==========================================================
                initial_image.main_image = False
                actual_url = initial_image.image_url
                
                # Pre-signal check
                assert initial_image._original_url == actual_url
                
                # Act: Save a different field
                initial_image.save(update_fields=['main_image'])
                
                # Post-signal check
                assert initial_image._original_url == actual_url
                
                
            # ==============================================================
            # POST-TRANSACTION: The queue is processed here
            # ==============================================================
            
            # Verify that only the first task (the one that changed the URL) was executed
            mock_delete.assert_called_once_with(urls=[old_url])
            
            # Total call count confirms Task 2 didn't add anything to the queue
            assert mock_delete.call_count == 1
            print("=" * 50 + "\n\n")


    def test_signal_cleanup_on_url_change(self, initial_image):
        """
        Ensures that updating the image_url triggers the physical file deletion 
        for the old asset.
        """
        img = initial_image 
        old_url = img.image_url  # Should be 'https://example.com/initial.jpg'
        new_url = 'https://example.com/media/realmente_cambio.jpg'

        # Intercept the physical storage deletion service
        with patch(self.TARGET_MOCK) as mock_delete:
            
            # Act: Update the URL and save. 
            # This triggers pre_save, schedules on_commit, and executes after the save completes.
            img.image_url = new_url
            img.save(update_fields=['image_url'])

            # Assert: Verify the cleanup service was called exactly once with the OLD URL
            mock_delete.assert_called_once_with(urls=[old_url])
            print("=" * 50 + "\n\n")
        

    def test_signal_no_delete_on_rollback(self, initial_image):
        """
        Verifies that physical files are NOT deleted if the database transaction 
        fails (Rollback).
        """
        old_url = initial_image.image_url
        
        with patch(self.TARGET_MOCK) as mock_delete:
            try:
                # Wrap the operation in an atomic block to simulate a failing transaction
                with transaction.atomic():
                    initial_image.image_url = "https://example.com/media/fallo.jpg"
                    initial_image.save(update_fields=['image_url'])
                    
                    # Force an exception to trigger a Rollback
                    raise ValueError("Controlled database failure")
            except ValueError:
                # Catch the exception to continue the test assertion
                pass

            # Verification:
            # Although the signal logic was reached (pre_save logs might appear), 
            # the on_commit hook must be discarded by Django due to the rollback.
            mock_delete.assert_not_called()
            
        # Ensure the DB record was reverted to its original state
        initial_image.refresh_from_db()
        assert initial_image.image_url == old_url
        print("=" * 50 + "\n\n")


    def test_signal_no_cleanup_when_url_stays_same(self, initial_image):
        """""
        Verifica que si cambio otro campo (ej: main_image), NO se intente borrar el archivo.
        """""
        with patch(self.TARGET_MOCK) as mock_delete:
            
            initial_image.main_image = False
            initial_image.save(update_fields=['main_image'])

            # No debería haberse llamado al borrado porque la URL no cambió
            mock_delete.assert_not_called()
        print("=" * 50 + "\n\n")  
        
        
    def test_signal_cleanup_on_delete(self, initial_image):
        """
        Verifica que al eliminar el registro, se borre el archivo físico.
        """
        url_to_delete = initial_image.image_url
        
        with patch(self.TARGET_MOCK) as mock_delete:
            initial_image.delete()
            
            mock_delete.assert_called_once_with(urls=[url_to_delete])
            print("=" * 50 + "\n\n") 
        
    