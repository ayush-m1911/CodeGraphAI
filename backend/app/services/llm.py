from groq import Groq

from app.config import settings

client = Groq(
    api_key=settings.groq_api_key
)


def generate_answer(
    context,
    question
):

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

    prompt = f"""
You are an expert software architect.

You are analyzing a source code repository.

You must use ONLY the provided repository context.

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