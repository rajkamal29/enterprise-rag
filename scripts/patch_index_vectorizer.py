"""
Patch rag-index to add an Azure OpenAI integrated vectorizer on the embedding field.
This allows the Agents API (vector_semantic_hybrid) to vectorize queries automatically.
"""
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    AzureOpenAIVectorizer,
    AzureOpenAIVectorizerParameters,
    HnswAlgorithmConfiguration,
    VectorSearch,
    VectorSearchProfile,
)

credential = DefaultAzureCredential()
client = SearchIndexClient(
    endpoint="https://srch-erag2-dev.search.windows.net",
    credential=credential,
)
idx = client.get_index("rag-index")

# Check existing vector search config
vs = idx.vector_search
print("Existing profiles:", [p.name for p in (vs.profiles or [])])
print("Existing algorithms:", [a.name for a in (vs.algorithms or [])])
print("Existing vectorizers:", [v.vectorizer_name for v in (vs.vectorizers or [])])

# Build the integrated vectorizer
vectorizer = AzureOpenAIVectorizer(
    vectorizer_name="openai-vectorizer",
    parameters=AzureOpenAIVectorizerParameters(
        resource_url="https://oai-erag2-dev.openai.azure.com/",
        deployment_name="text-embedding-3-large",
        model_name="text-embedding-3-large",
    ),
)

# Update vector search: keep existing algorithm/profile, add vectorizer
algorithms = vs.algorithms or [HnswAlgorithmConfiguration(name="default")]
profiles = vs.profiles or [
    VectorSearchProfile(name="default", algorithm_configuration_name=algorithms[0].name)
]

# Update profile to reference vectorizer
updated_profiles = []
for p in profiles:
    updated_profiles.append(
        VectorSearchProfile(
            name=p.name,
            algorithm_configuration_name=p.algorithm_configuration_name,
            vectorizer_name="openai-vectorizer",
        )
    )

idx.vector_search = VectorSearch(
    algorithms=algorithms,
    profiles=updated_profiles,
    vectorizers=[vectorizer],
)

# Also ensure the embedding field references the profile
for f in idx.fields:
    if f.name == "embedding":
        profile_name = getattr(f, "vector_search_profile_name", None)
        print(f"embedding field vector_search_profile: {profile_name}")
        if not getattr(f, "vector_search_profile_name", None) and updated_profiles:
            f.vector_search_profile_name = updated_profiles[0].name
        break

client.create_or_update_index(idx)
print("Vectorizer added successfully!")
