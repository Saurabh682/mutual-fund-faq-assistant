import re

def slugify(text: str) -> str:
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "_", slug)[:30]

def chunk_parsed_scheme(parsed_scheme: dict) -> list[dict]:
    scheme_id = parsed_scheme["scheme_id"]
    scheme_name = parsed_scheme["scheme_name"]
    url = parsed_scheme["url"]
    doc_date = parsed_scheme["doc_date"]
    sections = parsed_scheme.get("sections", [])

    chunks = []
    chunk_counter = 1

    for sec in sections:
        sec_title = sec["section"]
        content = sec["content"].strip()
        sec_slug = slugify(sec_title)

        # Size check: if content is moderately sized (standard section), keep atomic
        # This preserves key-value pairs and tables intact without fragmenting
        prefixed_text = f"{scheme_name} | {sec_title} | {content}"

        content_type = "faq_entry" if "FAQ" in sec_title else "section_paragraph"
        if any(term in sec_title.lower() for term in ["expense", "exit load", "minimums", "details"]):
            content_type = "table_row"

        chunk = {
            "chunk_id": f"{scheme_id}#{sec_slug}#c{chunk_counter}",
            "text": prefixed_text,
            "raw_content": content,
            "metadata": {
                "chunk_id": f"{scheme_id}#{sec_slug}#c{chunk_counter}",
                "scheme_id": scheme_id,
                "scheme_name": scheme_name,
                "section": sec_title,
                "url": url,
                "doc_date": str(doc_date),
                "priority": 1,
                "content_type": content_type
            }
        }
        chunks.append(chunk)
        chunk_counter += 1

    return chunks
