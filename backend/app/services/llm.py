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
    strategies_used=None,
    history=None
):
    """
    Generates a developer-targeted answer for the codebase question based on the retrieved contexts and multi-turn history.

    Args:
        context (list of dict): Code context chunks retrieved by the retrieval phase.
        question (str): User's question about the repository.
        intent (str, optional): The detected user intent.
        strategies_used (list of str, optional): The retrieval strategies executed.
        history (list of dict, optional): Prior conversation turns [{"role": "user"|"assistant", "content": "..."}].

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

    system_instruction = (
        "You are CodeGraphAI, an expert codebase intelligence and software architect assistant. "
        "You analyze source code repositories using AST parsing, vector search, and Neo4j knowledge graphs. "
        "You provide clear, accurate, and architectural explanations. "
        "Ground codebase-specific technical answers in the retrieved repository context chunks. "
        "For multi-turn conversational follow-ups, questions about earlier responses, or contextual queries, "
        "seamlessly leverage both the preceding conversation dialogue history and the repository context."
    )

    prompt = f"""{intent_metadata_block}
------------------------------------------------
Retrieved Repository Context:
{context_text if context_text.strip() else "(No new repository context chunks retrieved for this turn; use codebase knowledge & prior conversation dialogue history.)"}
------------------------------------------------
Question:
{question}
------------------------------------------------
Instructions:
1. Ground technical explanations in the provided code context and ongoing conversation history.
2. If the user is asking a follow-up, summary, or meta-question regarding earlier responses or topics in the chat, synthesize a clear, helpful answer referencing prior discussion.
3. Mention relevant file paths and symbol names when discussing codebase components.
4. Prefer architectural clarity and call flows over raw code dumping.
5. If specific codebase information is completely missing and cannot be answered from conversation history, concisely state what is missing.

Response Format:
Definition / Overview:
...

Files & Key Components:
...

Call Flow / Architecture:
...

Summary:
...
"""

    print("=" * 80)
    print(context_text[:3000])
    print("=" * 80)

    try:
        messages = [{"role": "system", "content": system_instruction}]
        if history:
            for turn in history:
                messages.append({
                    "role": turn.get("role", "user"),
                    "content": turn.get("content", "")
                })
        messages.append({
            "role": "user",
            "content": prompt
        })

        # Prioritize configured openai/gpt-oss-120b model with resilient fallbacks
        primary_model = getattr(settings, "llm_model", "openai/gpt-oss-120b")
        model_candidates = [
            primary_model,
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama-3.1-70b-versatile",
            "llama-3.1-8b-instant",
            "llama3-70b-8192",
            "llama3-8b-8192"
        ]
        # Deduplicate while preserving order
        unique_models = []
        for m in model_candidates:
            if m not in unique_models:
                unique_models.append(m)

        response = None
        for model_name in unique_models:
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0
                )
                if response and response.choices:
                    return response.choices[0].message.content
            except Exception:
                continue

        raise RuntimeError("All LLM model candidates failed")


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