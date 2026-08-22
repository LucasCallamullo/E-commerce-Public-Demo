import pytest
from django.urls import reverse
from home.models.social_media import SocialMedia

@pytest.mark.django_db
class TestSocialMediaAPI:
    """
    Test suite for Social Media API operations.
    Covers partial updates (PATCH), business logic constraints for 'main' networks,
    and visibility consistency rules.
    """
    
    @pytest.fixture
    def url_list(self, store_data):
        """Returns the URL for the social media list/create endpoint."""
        return reverse('api_store_networks', kwargs={'store_id': store_data.id})

    @staticmethod
    def url_detail(store, network):
        """
        Static helper to generate the detail URL for a specific social network.
        Allows flexible URL generation without relying on a fixed fixture.
        """
        return reverse('api_store_networks_detail', kwargs={
            'store_id': store.id, 
            'network_id': network.id
        })

    @pytest.fixture
    def initial_networks(self, store_data):
        """
        Fixture that populates the database with a standard set of social networks.
        Sets the first 4 as 'is_main=True' to test boundary conditions for the 
        maximum main networks limit.
        """
        default_platforms = {
            SocialMedia.PlatformEnum.GG: "https://google.com/",
            SocialMedia.PlatformEnum.IG: "https://instagram.com/",
            SocialMedia.PlatformEnum.FB: "https://facebook.com/",
            SocialMedia.PlatformEnum.TT: "https://www.tiktok.com",
            SocialMedia.PlatformEnum.TW: "https://x.com/home",
            SocialMedia.PlatformEnum.YT: "https://www.youtube.com",
            SocialMedia.PlatformEnum.GM: "https://google.com/maps",
        }
        
        networks_to_create = []
        count = 0
        for plat, url in default_platforms.items():
            count += 1
            obj = SocialMedia(
                store=store_data,
                platform=plat,
                url=url,
                is_active=True,
                is_main=(count <= 4)  # First 4 are main, remaining are not.
            )
            networks_to_create.append(obj)
        
        return SocialMedia.objects.bulk_create(networks_to_create)
    
    @pytest.fixture
    def last_network(self, initial_networks):
        """Returns the last network in the set (initialized as is_main=False)."""
        return initial_networks[-1]
    
    @pytest.fixture
    def first_network(self, initial_networks):
        """Returns the first network in the set (initialized as is_main=True)."""
        return initial_networks[0]
    
    @pytest.fixture
    def initial_network(self, store_data):
        """Creates a single standalone network for basic operation tests."""
        return SocialMedia.objects.create(
            store=store_data,
            platform=SocialMedia.PlatformEnum.GG,
            url="https://google.com/",
            is_active=True
        )

    # --- PATCH TESTS (Updates) ---

    def test_limit_4_is_main_error(self, auth_client, store_data, last_network):
        """
        Verifies that setting a 5th network as 'main' triggers a 400 error.
        Ensures business logic prevents exceeding the 4-main-network cap.
        """
        data = {'is_main': True}
        response = auth_client.patch(
            TestSocialMediaAPI.url_detail(store=store_data, network=last_network), 
            data, format='json'
        )
        assert 'No puede tener más de 4 Redes Principales' in str(response.data)
        assert response.status_code == 400
        last_network.refresh_from_db()
        assert last_network.platform == SocialMedia.PlatformEnum.GM 
        
    def test_limit_4_is_main_success(self, auth_client, store_data, first_network):
        """
        Ensures that updating a network that is already 'main' does not trigger 
        the limit error, allowing metadata updates (like URLs).
        """
        data = {'url': "https://google.com/"}
        response = auth_client.patch(
            TestSocialMediaAPI.url_detail(store=store_data, network=first_network), 
            data, format='json'
        )
        assert response.status_code == 200
        first_network.refresh_from_db()
        assert first_network.platform == SocialMedia.PlatformEnum.GG
        assert first_network.url == "https://google.com/"
        assert first_network.is_main == True
    
    def test_patch_is_main(self, auth_client, store_data, initial_network):
        """Tests partial update functionality for promoting a network to 'main'."""
        data = {'is_main': True}
        response = auth_client.patch(
            TestSocialMediaAPI.url_detail(store=store_data, network=initial_network), 
            data, format='json'
        )
        
        assert response.status_code == 200
        initial_network.refresh_from_db()
        
        assert initial_network.url == "https://google.com/"
        assert initial_network.platform == SocialMedia.PlatformEnum.GG
        assert initial_network.is_main == True 
        assert initial_network.is_active == True
        
    def test_patch_is_main_error(self, auth_client, store_data, initial_network):
        """Tests that a network cannot be set as 'main' while being 'inactive'."""
        data = {'is_active': False, 'is_main': True}
        
        response = auth_client.patch(
            TestSocialMediaAPI.url_detail(store=store_data, network=initial_network), 
            data, format='json'
        )
        
        assert response.status_code == 400
        initial_network.refresh_from_db()
        
        assert initial_network.is_main == False 
        assert initial_network.is_active == True
