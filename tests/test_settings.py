"""Tests for AzureSettings – env-var loading and validation."""


import pytest

from config.settings import AzureSettings


class TestAzureSettingsDefaults:
    def test_all_string_fields_default_to_empty(self) -> None:
        settings = AzureSettings()
        assert settings.azure_openai_endpoint == ""
        assert settings.azure_search_endpoint == ""
        assert settings.azure_keyvault_url == ""
        assert settings.azure_ai_foundry_project_connection_string == ""
        assert settings.azure_client_id == ""

    def test_default_api_version(self) -> None:
        settings = AzureSettings()
        assert settings.azure_openai_api_version == "2024-08-01-preview"

    def test_default_deployments(self) -> None:
        settings = AzureSettings()
        assert settings.azure_openai_chat_deployment == "gpt-4o"
        assert settings.azure_openai_embedding_deployment == "text-embedding-3-large"

    def test_default_index_name(self) -> None:
        settings = AzureSettings()
        assert settings.azure_search_index_name == "rag-index"


class TestAzureSettingsEnvOverride:
    def test_openai_endpoint_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://my-oai.openai.azure.com/")
        settings = AzureSettings()
        # Trailing slash should be stripped
        assert settings.azure_openai_endpoint == "https://my-oai.openai.azure.com"

    def test_search_endpoint_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://my-srch.search.windows.net/")
        settings = AzureSettings()
        assert settings.azure_search_endpoint == "https://my-srch.search.windows.net"

    def test_keyvault_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_KEYVAULT_URL", "https://kv-erag-dev.vault.azure.net/")
        settings = AzureSettings()
        assert settings.azure_keyvault_url == "https://kv-erag-dev.vault.azure.net"

    def test_custom_index_name_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_SEARCH_INDEX_NAME", "custom-index")
        settings = AzureSettings()
        assert settings.azure_search_index_name == "custom-index"

    def test_foundry_connection_string_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        conn = "eastus.api.azureml.ms;sub-id;rg-dev;proj-dev"
        monkeypatch.setenv("AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING", conn)
        settings = AzureSettings()
        assert settings.azure_ai_foundry_project_connection_string == conn


class TestAzureSettingsConfiguredProperties:
    def test_not_configured_when_empty(self) -> None:
        settings = AzureSettings()
        assert not settings.openai_is_configured
        assert not settings.search_is_configured
        assert not settings.keyvault_is_configured
        assert not settings.foundry_is_configured

    def test_openai_configured_when_endpoint_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://oai.openai.azure.com")
        settings = AzureSettings()
        assert settings.openai_is_configured

    def test_search_configured_when_endpoint_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_SEARCH_ENDPOINT", "https://srch.search.windows.net")
        settings = AzureSettings()
        assert settings.search_is_configured

    def test_keyvault_configured_when_url_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("AZURE_KEYVAULT_URL", "https://kv.vault.azure.net")
        settings = AzureSettings()
        assert settings.keyvault_is_configured

    def test_foundry_configured_when_conn_str_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv(
            "AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING",
            "eastus.api.azureml.ms;sub;rg;proj",
        )
        settings = AzureSettings()
        assert settings.foundry_is_configured


class TestTrailingSlashStripping:
    @pytest.mark.parametrize("endpoint_env, field", [
        ("AZURE_OPENAI_ENDPOINT", "azure_openai_endpoint"),
        ("AZURE_SEARCH_ENDPOINT", "azure_search_endpoint"),
        ("AZURE_KEYVAULT_URL", "azure_keyvault_url"),
    ])
    def test_trailing_slash_stripped(
        self,
        monkeypatch: pytest.MonkeyPatch,
        endpoint_env: str,
        field: str,
    ) -> None:
        monkeypatch.setenv(endpoint_env, "https://example.azure.com/")
        settings = AzureSettings()
        assert not getattr(settings, field).endswith("/")
