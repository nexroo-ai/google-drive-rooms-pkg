from unittest.mock import Mock, patch

import pytest

from google_drive_rooms_pkg.addon import GoogleDriveRoomsAddon


class TestGoogleDriveRoomsAddon:
    def test_addon_initialization(self):
        addon = GoogleDriveRoomsAddon()

        assert addon.type == "cloud_storage"
        assert addon.modules == ["actions", "configuration", "memory", "services", "storage", "tools", "utils"]
        assert addon.config == {}
        assert addon.credentials is not None
        assert addon.tool_registry is not None
        assert addon.observer_callback is None
        assert addon.addon_id is None

    def test_logger_property(self):
        addon = GoogleDriveRoomsAddon()
        logger = addon.logger

        assert hasattr(logger, 'debug')
        assert hasattr(logger, 'info')
        assert hasattr(logger, 'warning')
        assert hasattr(logger, 'error')
        assert logger.addon_type == "cloud_storage"


    def test_load_tools(self, sample_tools, sample_tool_descriptions):
        addon = GoogleDriveRoomsAddon()

        with patch.object(addon.tool_registry, 'register_tools') as mock_register, \
             patch.object(addon.tool_registry, 'get_tools_for_action', return_value={"tool1": {}, "tool2": {}}):

            addon.loadTools(sample_tools, sample_tool_descriptions)

            mock_register.assert_called_once_with(sample_tools, sample_tool_descriptions, None)

    def test_get_tools(self):
        addon = GoogleDriveRoomsAddon()
        expected_tools = {"tool1": {"name": "tool1"}, "tool2": {"name": "tool2"}}

        with patch.object(addon.tool_registry, 'get_tools_for_action', return_value=expected_tools):
            result = addon.getTools()

            assert result == expected_tools

    def test_clear_tools(self):
        addon = GoogleDriveRoomsAddon()

        with patch.object(addon.tool_registry, 'clear') as mock_clear:
            addon.clearTools()

            mock_clear.assert_called_once()

    def test_set_observer_callback(self):
        addon = GoogleDriveRoomsAddon()
        callback = Mock()
        addon_id = "test_addon"

        addon.setObserverCallback(callback, addon_id)

        assert addon.observer_callback == callback
        assert addon.addon_id == addon_id

    def test_download_document_action(self):
        addon = GoogleDriveRoomsAddon()

        from google_drive_rooms_pkg.configuration import CustomAddonConfig

        test_config = CustomAddonConfig(
            id="test-drive",
            type="google_drive",
            name="Test Drive",
            description="Test Google Drive addon",
            secrets={"google_drive_access_token": "fake_token"}
        )
        addon.config = test_config

        with patch('google_drive_rooms_pkg.actions.download_document.requests.get') as mock_get:
            mock_get.return_value.status_code = 401
            mock_get.return_value.json.return_value = {"error": {"message": "Invalid token"}}

            result = addon.download_document(fileId="test_file_id")

            from google_drive_rooms_pkg.actions.base import ActionResponse
            assert isinstance(result, ActionResponse)
            assert result.code == 401
            assert result.message == "Invalid token"

    def test_load_addon_config_success(self, sample_config):
        addon = GoogleDriveRoomsAddon()

        with patch('google_drive_rooms_pkg.configuration.CustomAddonConfig') as MockConfig:
            mock_config_instance = Mock()
            MockConfig.return_value = mock_config_instance

            result = addon.loadAddonConfig(sample_config)

            MockConfig.assert_called_once_with(**sample_config)
            assert addon.config == mock_config_instance
            assert result is True

    def test_load_addon_config_failure(self):
        addon = GoogleDriveRoomsAddon()

        with patch('google_drive_rooms_pkg.configuration.CustomAddonConfig', side_effect=Exception("Config error")):
            result = addon.loadAddonConfig({})

            assert result is False

    def test_load_credentials_success(self, sample_credentials):
        addon = GoogleDriveRoomsAddon()

        with patch.object(addon.credentials, 'store_multiple') as mock_store:
            result = addon.loadCredentials(**sample_credentials)

            mock_store.assert_called_once_with(sample_credentials)
            assert result is True

    def test_load_credentials_with_config_validation(self, sample_credentials):
        addon = GoogleDriveRoomsAddon()
        mock_config = Mock()
        mock_config.secrets = {"API_KEY": "required", "DATABASE_URL": "required"}
        addon.config = mock_config

        with patch.object(addon.credentials, 'store_multiple') as mock_store:
            result = addon.loadCredentials(**sample_credentials)

            mock_store.assert_called_once_with(sample_credentials)
            assert result is True

    def test_load_credentials_missing_required_secrets(self):
        addon = GoogleDriveRoomsAddon()
        mock_config = Mock()
        mock_config.secrets = {"REQUIRED_SECRET": "required", "ANOTHER_SECRET": "required"}
        addon.config = mock_config

        result = addon.loadCredentials(REQUIRED_SECRET="value")

        assert result is False

    def test_load_credentials_failure(self, sample_credentials):
        addon = GoogleDriveRoomsAddon()

        with patch.object(addon.credentials, 'store_multiple', side_effect=Exception("Store error")):
            result = addon.loadCredentials(**sample_credentials)

            assert result is False

    def test_test_method_success(self):
        addon = GoogleDriveRoomsAddon()

        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.__all__ = ['TestComponent']
            mock_module.TestComponent = Mock()
            mock_import.return_value = mock_module

            result = addon.test()

            assert result is True

    def test_test_method_import_error(self):
        addon = GoogleDriveRoomsAddon()

        with patch('importlib.import_module', side_effect=ImportError("Module not found")):
            result = addon.test()

            assert result is False

    def test_test_method_general_error(self):
        addon = GoogleDriveRoomsAddon()

        with patch('importlib.import_module', side_effect=Exception("General error")):
            result = addon.test()

            assert result is False

    def test_test_method_component_skip_pydantic(self):
        addon = GoogleDriveRoomsAddon()

        with patch('importlib.import_module') as mock_import:
            from pydantic import BaseModel

            class TestModel(BaseModel):
                pass

            mock_module = Mock()
            mock_module.__all__ = ['TestModel']
            mock_module.TestModel = TestModel
            mock_import.return_value = mock_module

            result = addon.test()

            assert result is True

    def test_test_method_component_skip_known_models(self):
        addon = GoogleDriveRoomsAddon()

        with patch('importlib.import_module') as mock_import:
            mock_module = Mock()
            mock_module.__all__ = ['ActionInput', 'ActionOutput']
            mock_module.ActionInput = Mock
            mock_module.ActionOutput = Mock
            mock_import.return_value = mock_module

            result = addon.test()

            assert result is True

