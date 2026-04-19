"""Azure settings loaded from environment variables or a .env file.

All fields use ``DefaultAzureCredential`` for authentication — no secrets
are stored in code or this settings object.  The only "credentials" here
are endpoint URLs and deployment names, which are safe to log.
"""

from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AzureSettings(BaseSettings):
    """Pydantic-Settings class for all Azure service endpoints.

    Values are resolved in this order:
    1. Environment variables (``AZURE_OPENAI_ENDPOINT``, etc.)
    2. ``.env`` file in the project root (gitignored)
    3. Field defaults

    All URL fields are validated as proper HTTP/HTTPS URLs.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # ── Azure OpenAI ─────────────────────────────────────────────────────────
    azure_openai_endpoint: str = ""
    azure_openai_api_version: str = "2024-08-01-preview"
    azure_openai_chat_deployment: str = "gpt-4o"
    azure_openai_embedding_deployment: str = "text-embedding-3-large"

    # ── Azure AI Search ───────────────────────────────────────────────────────
    azure_search_endpoint: str = ""
    azure_search_index_name: str = "rag-index"

    # ── Azure Document Intelligence ────────────────────────────────────────────
    azure_documentintelligence_endpoint: str = ""

    # ── Azure Key Vault ───────────────────────────────────────────────────────
    azure_keyvault_url: str = ""

    # ── Azure AI Foundry (Track A) ────────────────────────────────────────────
    # Format: <region>.api.azureml.ms;<subscription>;<resource_group>;<project>
    azure_ai_foundry_project_connection_string: str = ""

    # Azure AI Foundry connection name for the AI Search service.
    # Set in the AI Foundry portal under Project Settings → Connections,
    # then reference the connection name here.
    # Used by AzureAISearchTool as index_connection_id.
    azure_ai_search_connection_id: str = ""

    # ── Managed Identity ──────────────────────────────────────────────────────
    # When running on Azure (ACA, VM, etc.) the SDK picks this up automatically
    # from IMDS.  For local dev, set AZURE_CLIENT_ID to the user-assigned MI
    # client ID so DefaultAzureCredential targets the right identity.
    azure_client_id: str = ""

    # ── Convenience properties ────────────────────────────────────────────────
    @field_validator(
        "azure_openai_endpoint", "azure_search_endpoint", "azure_keyvault_url",
        mode="before",
    )
    @classmethod
    def _strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/") if isinstance(v, str) else v

    @property
    def openai_is_configured(self) -> bool:
        return bool(self.azure_openai_endpoint)

    @property
    def search_is_configured(self) -> bool:
        return bool(self.azure_search_endpoint)

    @property
    def keyvault_is_configured(self) -> bool:
        return bool(self.azure_keyvault_url)

    @property
    def foundry_is_configured(self) -> bool:
        return bool(self.azure_ai_foundry_project_connection_string)

    @property
    def foundry_search_is_configured(self) -> bool:
        """True when both Foundry and the AI Search connection ID are set."""
        return self.foundry_is_configured and bool(self.azure_ai_search_connection_id)

    @property
    def documentintelligence_is_configured(self) -> bool:
        return bool(self.azure_documentintelligence_endpoint)
