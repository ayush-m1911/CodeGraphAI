"""
Purpose:
Manages interaction with LLMs to generate source-grounded answers.

Role in CodeGraphAI:
The final stage of the GraphRAG pipeline. It formats retrieved code context chunks (from vectors, symbol lookup,
and graph paths) and queries the Groq API for responses. It includes a fallback logic that synthesizes a structured,
metadata-enriched answer locally if the API limit is hit or credentials are not found.

GraphRAG Workflow:

Question
↓
Vector Retrieval
↓
Symbol Expansion
↓
Knowledge Graph
↓
LLM
↓
Answer

Key Responsibilities:
* Truncate and compile context chunks safely under maximum token/character limits.
* Formulate system instructions that require the LLM to output source-grounded references and call flows.
* Execute completions requests against Groq using Llama 3.3.
* Provide an automated, structural local summary fallback if the Groq API key is invalid or network issues occur.
"""

from groq import Groq

from app.config import settings

client = Groq(
    api_key=settings.groq_api_key
)


def generate_answer(
    context,
    question,
    intent=None,
    strategies_used=None
):
    """
    Generates a developer-targeted answer for the codebase question based on the retrieved contexts.

    Workflow:
    1. Filter and format context chunks (file paths, symbols, relation details, code snippets) up to character boundaries.
    2. Construct structured instructions enforcing definitions, files, call flows, and related components list.
    3. Include intent and strategies_used metadata in the prompt to assist reasoning.
    4. Make a chat completion call to Groq with llama-3.3-70b-versatile.
    5. If it fails, compile an AST structural explanation locally based on retrieved context metadata to prevent runtime errors.

    Args:
        context (list of dict): Code context chunks retrieved by the retrieval phase.
        question (str): User's question about the repository.
        intent (str, optional): The detected user intent.
        strategies_used (list of str, optional): The retrieval strategies executed.

    Returns:
        str: Grounded response answer in markdown formatting.
    """

    MAX_CONTEXT_CHARS = 7000

    context_parts = []
    current_size = 0

    for chunk in context:

        chunk_text = f"""
FILE: {chunk.get('file_path', 'unknown')}

TYPE: {chunk.get('chunk_type', 'unknown')}

SYMBOL: {chunk.get('symbol_name', 'unknown')}

RELATION: {chunk.get('relation', 'none')}

CODE:

{chunk.get('text', '')[:1200]}
"""

        if (
            current_size
            + len(chunk_text)
            > MAX_CONTEXT_CHARS
        ):
            break

        context_parts.append(
            chunk_text
        )

        current_size += len(
            chunk_text
        )

    context_text = "\n\n".join(
        context_parts
    )

    intent_metadata_block = ""
    if intent:
        intent_metadata_block = f"""
------------------------------------------------

Retrieval Metadata:
Intent: {intent}
Retrieval Strategy: {", ".join(strategies_used or [])}
"""

    prompt = f"""
You are an expert software architect.

You are analyzing a source code repository.

You must use ONLY the provided repository context.
{intent_metadata_block}
------------------------------------------------

Repository Context:

{context_text}

------------------------------------------------

Question:

{question}

------------------------------------------------

Instructions:

1. Explain where the requested class, function, or method is defined.

2. Mention the exact file names involved.

3. Use graph relationships when available.

4. Explain call flows.

5. Explain parent-child relationships.

6. Explain dependencies.

7. Explain how components interact.

8. If multiple files participate, explain the chain.

9. Prefer architectural explanations over code dumping.

10. If information is missing from context, explicitly say so.

------------------------------------------------

Response Format:

Definition:
...

Files:
...

Call Flow:
...

Related Components:
...

Summary:
...
"""

    print("=" * 80)
    print(context_text[:3000])
    print("=" * 80)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0
        )

        return response.choices[
            0
        ].message.content
    except Exception as e:
        print(f"Groq API call failed: {e}. Generating context-based fallback response.")
        
        if not context:
            return f"### Definition:\nNo context could be retrieved for the query: **{question}**.\n\n### Files:\n- None\n\n### Call Flow:\n- No call flow context retrieved.\n\n### Related Components:\n- None\n\n### Summary:\nUnable to find references in the repository index. Please verify that the repository has been parsed and contains python source files."
            
        first_chunk = context[0]
        file_path = first_chunk.get("file_path", "unknown")
        symbol_name = first_chunk.get("symbol_name", "unknown")
        chunk_type = first_chunk.get("chunk_type", "unknown")
        
        files_list = sorted(list(set(c.get("file_path") for c in context if c.get("file_path"))))
        files_md = "\n".join(f"- `{f}`" for f in files_list)
        
        flow_parts = []
        for c in context:
            if c.get("relation") and c.get("graph_source"):
                flow_parts.append(f"- `{c.get('graph_source')}` **{c.get('relation')}** `{c.get('symbol_name')}` (in `{c.get('file_path')}`)")
        flow_md = "\n".join(flow_parts) if flow_parts else "- No direct call relations in retrieved chunks."
        
        fallback_answer = f"""### Definition:
The query centers on structural elements in the repository. The retrieved codebase context points to class/function definitions in `{file_path}` relating to `{symbol_name}`.

### Files:
{files_md}

### Call Flow:
{flow_md}

### Related Components:
- **Symbol**: `{symbol_name}` (type: `{chunk_type}`)
- **Retrieved Chunk Content (excerpt)**:
```python
{first_chunk.get('text', '')[:600]}
```

### Summary:
*(Fallback Response due to Groq API connection limit)*
The codebase defines `{symbol_name}` as a `{chunk_type}` in file `{file_path}`. Based on exact symbol matches and GraphRAG connections, it is associated with elements across {len(files_list)} file(s). You can explore its relationships and dependencies in the right-side GraphRAG Context Panel or check the source blocks below.
"""
        return fallback_answer