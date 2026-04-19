"""
Inspect the rag-index schema and patch it with semantic + vector config if missing.
"""

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)

credential = DefaultAzureCredential()
client = SearchIndexClient(
    endpoint="https://srch-erag2-dev.search.windows.net",
    credential=credential,
)

idx = client.get_index("rag-index")

print("Fields:")
for f in idx.fields:
    print(f"  {f.name}: {f.type}")

print()
print("Semantic config:", idx.semantic_search)
print("Vector search:", idx.vector_search)

# Check if semantic config is missing
if not idx.semantic_search or not idx.semantic_search.configurations:
    print()
    print("No semantic configuration found — patching...")

    # Find likely content/text field
    text_fields = [f.name for f in idx.fields if "Edm.String" in str(f.type)]
    print("String fields:", text_fields)

    # Build semantic config using common field names
    content_field = next((f for f in text_fields if "content" in f.lower()), None)
    title_field = next((f for f in text_fields if "title" in f.lower()), None)

    print(f"Using content_field={content_field}, title_field={title_field}")

    if content_field:
        sem_config = SemanticConfiguration(
            name="default",
            prioritized_fields=SemanticPrioritizedFields(
                content_fields=[SemanticField(field_name=content_field)],
                title_field=SemanticField(field_name=title_field) if title_field else None,
            ),
        )
        idx.semantic_search = SemanticSearch(
            configurations=[sem_config], default_configuration_name="default"
        )
        client.create_or_update_index(idx)
        print("Semantic config added successfully!")
    else:
        print("Could not identify content field. Index fields above — update manually.")
else:
    print("Semantic configuration already exists.")
    for sc in idx.semantic_search.configurations:
        print(f"  Config: {sc.name}")
