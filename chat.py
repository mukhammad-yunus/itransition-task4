import json

def ask_gemini(client, question, store_name, statistics):

    # Create a compact summary of the data.
    context = {
        "store": store_name,
        "statistics": statistics
    }

    prompt = f"""
You are a data analysis assistant for a book sales dashboard.

Answer the user's question using the supplied data.

Rules:
- Do not invent statistics or facts.
- State when the supplied data is insufficient.
- Distinguish observed facts from possible explanations.
- Do not claim that a sample represents the entire dataset.
- Do not perform unsupported calculations.

Store data:
{json.dumps(context, default=str)}

User question:
{question}
"""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
    )

    return response.text