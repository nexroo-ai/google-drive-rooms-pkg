import pytest
from pydantic import ValidationError

from google_drive_rooms_pkg.configuration.addonconfig import CustomAddonConfig
from google_drive_rooms_pkg.configuration.baseconfig import BaseAddonConfig


class TestBaseAddonConfig:
    def test_base_config_creation(self):
        config = BaseAddonConfig(
            id="test_addon_id",
            type="test_type",
            name="test_addon",
            description="Test addon description",
            secrets={"key1": "value1"}
        )

        assert config.id == "test_addon_id"
        assert config.type == "test_type"
        assert config.name == "test_addon"
        assert config.description == "Test addon description"
        assert config.secrets == {"key1": "value1"}
        assert config.enabled is True

    def test_base_config_defaults(self):
        config = BaseAddonConfig(
            id="test_id",
            type="test_type",
            name="test",
            description="Test description"
        )

        assert config.enabled is True
        assert config.secrets == {}
        assert config.config == {}


class TestCustomAddonConfig:
    def test_custom_config_creation_success(self):
        config = CustomAddonConfig(
            id="test_drive_addon_id",
            type="google_drive",
            name="test_drive_addon",
            description="Test Google Drive addon",
            page_size=50,
            max_page_size=500,
            max_download_size_mb=25,
            secrets={"google_drive_access_token": "test_token"}
        )

        assert config.id == "test_drive_addon_id"
        assert config.name == "test_drive_addon"
        assert config.type == "google_drive"
        assert config.page_size == 50
        assert config.max_page_size == 500
        assert config.max_download_size_mb == 25

    def test_custom_config_with_defaults(self):
        config = CustomAddonConfig(
            id="test_drive_addon_id",
            type="google_drive",
            name="test_drive_addon",
            description="Test Google Drive addon",
            secrets={"google_drive_access_token": "test_token"}
        )

        assert config.page_size == 100
        assert config.max_page_size == 1000
        assert config.max_download_size_mb == 50

    def test_custom_config_missing_access_token(self):
        with pytest.raises(ValidationError, match="Missing Google Drive secrets"):
            CustomAddonConfig(
                id="test_drive_addon_id",
                type="google_drive",
                name="test_drive_addon",
                description="Test Google Drive addon",
                secrets={}
            )

    def test_custom_config_with_wrong_secret_key(self):
        with pytest.raises(ValidationError, match="Missing Google Drive secrets"):
            CustomAddonConfig(
                id="test_drive_addon_id",
                type="google_drive",
                name="test_drive_addon",
                description="Test Google Drive addon",
                secrets={"wrong_key": "value"}
            )

    def test_custom_config_missing_required_fields(self):
        with pytest.raises(ValidationError):
            CustomAddonConfig(
                id="test_db_addon_id",
            type="google_drive",
                name="test_db_addon",
                description="Test database addon",
                secrets={"db_password": "secret", "db_user": "user"}
            )
