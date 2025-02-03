from agents.blog_team.schema import BlogPost
from langchain.docstore.document import Document


def blog_post_to_document(blog_post: BlogPost) -> Document:
    """Convert a BlogPost object to a Document object"""
    # Convert FAQ list to string if exists
    faq_str = (
        "\n".join([f"Q: {faq.question}\nA: {faq.answer}" for faq in blog_post.faq_list])
        if blog_post.faq_list
        else ""
    )

    # Flatten metadata
    flat_metadata = {
        "title": blog_post.title,
        "url": blog_post.url,
        "published_date": blog_post.published_date if blog_post.published_date else "",
        "summary": blog_post.summary if blog_post.summary else "",
    }
    if blog_post.metadata:
        flat_metadata.update(
            {
                meta.key: meta.value
                for meta in blog_post.metadata
                if meta.key and meta.value
            }
        )

    # Combine content
    content = f"{blog_post.content}\n\nFAQs:\n{faq_str}"

    return Document(page_content=content, metadata=flat_metadata)
