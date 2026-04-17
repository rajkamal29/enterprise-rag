"""Azure client factory.

All clients are created with ``DefaultAzureCredential``, which resolves
authentication in this order when running locally:
  1. Environment variables (``AZURE_CLIENT_ID`` / ``AZURE_TENANT_ID`` / ``AZURE_CLIENT_SECRET``)
  2. Azure CLI (``az login``)
  3. Visual Studio Code credential

When running on Azure (Container Apps, VM, etc.) the Managed Identity
credential is used automatically.

Clients are instantiated lazily and cached per factory instance.
"""

from __future__ import annotations

from functools import cached_property

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from openai import AzureOpenAI

from config.settings import AzureSettings


class AzureClientFactory:
    """Creates and caches Azure SDK clients for a given settings configuration."""

    def __init__(self, settings: AzureSettings) -> None:
        self._settings = settings

    # ── Shared credential ────────────────────────────────────────────────────
    @cached_property
    def credential(self) -> DefaultAzureCredential:
        """Single ``DefaultAzureCredential`` instance shared across all clients."""
        kwargs: dict[str, str] = {}
        if self._settings.azure_client_id:
            # Target a specific user-assigned managed identity by client ID.
            kwargs["managed_identity_client_id"] = self._settings.azure_client_id
        return DefaultAzureCredential(**kwargs)

    # ── Azure OpenAI ─────────────────────────────────────────────────────────
    @cached_property
    def openai_client(self) -> AzureOpenAI:
        """AzureOpenAI client authenticated via DefaultAzureCredential."""
        if not self._settings.openai_is_configured:
            raise RuntimeError(
                "AZURE_OPENAI_ENDPOINT is not set. "
                "Run infra/deploy.ps1 and source the generated .env file."
            )
        from azure.identity import get_bearer_token_provider

        token_provider = get_bearer_token_provider(
            self.credential,
            "https://cognitiveservices.azure.com/.default",
        )
        return AzureOpenAI(
            azure_endpoint=self._settings.azure_openai_endpoint,
            azure_deployment=self._settings.azure_openai_chat_deployment,
            api_version=self._settings.azure_openai_api_version,
            azure_ad_token_provider=token_provider,
        )

    # ── Azure AI Search ───────────────────────────────────────────────────────
    @cached_property
    def search_client(self) -> SearchClient:
        """SearchClient for the configured index, authenticated via Entra ID."""
        if not self._settings.search_is_configured:
            raise RuntimeError(
                "AZURE_SEARCH_ENDPOINT is not set. "
                "Run infra/deploy.ps1 and source the generated .env file."
            )
        return SearchClient(
            endpoint=self._settings.azure_search_endpoint,
            index_name=self._settings.azure_search_index_name,
            credential=self.credential,
        )

    @cached_property
    def search_index_client(self) -> SearchIndexClient:
        """SearchIndexClient for creating/managing indexes."""
        if not self._settings.search_is_configured:
            raise RuntimeError("AZURE_SEARCH_ENDPOINT is not set.")
        return SearchIndexClient(
            endpoint=self._settings.azure_search_endpoint,
            credential=self.credential,
        )

    # ── Azure Key Vault ───────────────────────────────────────────────────────
    @cached_property
    def keyvault_client(self) -> SecretClient:
        """Key Vault SecretClient authenticated via Entra ID."""
        if not self._settings.keyvault_is_configured:
            raise RuntimeError(
                "AZURE_KEYVAULT_URL is not set. "
                "Run infra/deploy.ps1 and source the generated .env file."
            )
        return SecretClient(
            vault_url=self._settings.azure_keyvault_url,
            credential=self.credential,
        )

    # ── Azure AI Foundry (Track A) ────────────────────────────────────────────
    def ai_foundry_project_client(self) -> object:
        """AIProjectClient for the AI Foundry project (Track A).

        Returns an ``azure.ai.projects.AIProjectClient`` instance.
        Import is deferred to avoid hard failure when the package is not
        installed or the connection string is not configured.
        """
        if not self._settings.foundry_is_configured:
            raise RuntimeError(
                "AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING is not set. "
                "Run infra/deploy.ps1 and source the generated .env file."
            )
        try:
            from azure.ai.projects import AIProjectClient
        except ImportError as exc:
            raise ImportError(
                "azure-ai-projects is required for Track A. "
                "It should already be installed; run `uv sync`."
            ) from exc

        # Stored format: <region>.api.azureml.ms;<subscription>;<resource_group>;<project>
        # AIProjectClient expects an endpoint URL ending with /api/projects/<project>.
        conn_parts = self._settings.azure_ai_foundry_project_connection_string.split(";")
        if len(conn_parts) != 4:
            raise ValueError(
                "AZURE_AI_FOUNDRY_PROJECT_CONNECTION_STRING has invalid format. "
                "Expected '<region>.api.azureml.ms;<subscription>;<resource_group>;<project>'."
            )

        host, _, _, project_name = conn_parts
        endpoint = f"https://{host}/api/projects/{project_name}"

        return AIProjectClient(
            endpoint=endpoint,
            credential=self.credential,
        )
