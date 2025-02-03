from pydantic import BaseModel, Field
from typing import Optional, List


class FAQItem(BaseModel):
    question: str = Field(description="The FAQ question")
    answer: str = Field(description="The answer to the FAQ")


class Metadata(BaseModel):
    key: str = Field(description="The metadata key")
    value: str = Field(description="The metadata value")


class BlogPost(BaseModel):
    title: str = Field(description="The title of the blog post")
    content: str = Field(description="The main content of the blog post")
    url: str = Field(description="The URL of the blog post")
    faq_list: Optional[List[FAQItem]] = Field(
        default=None, description="A list of FAQ items found in the blog post"
    )
    published_date: Optional[str] = Field(
        default=None, description="The publication date of the blog post"
    )
    summary: Optional[str] = Field(
        default=None, description="A brief summary of the blog post"
    )
    metadata: Optional[List[Metadata]] = Field(
        default=None, description="A list of key elements found in the blog post"
    )
