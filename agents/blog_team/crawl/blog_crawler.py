from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI

from typing import List, AsyncGenerator

from agents.blog_team.vectorstore.handler import VectorStoreHandler
from agents.blog_team.schema import BlogPost


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.decompose()

    # Get text and remove extra whitespace
    text = soup.get_text(separator="\n")
    cleaned_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    return cleaned_text


async def crawl_blog_urls(use_cached=False) -> List[str]:
    """
    Crawls tahagasht.com to extract URLs of blog posts
    """
    if use_cached:
        with open("blog_urls.txt", "r") as f:
            return f.read().splitlines()

    base_url = "https://www.tahagasht.com/weblog/sitemap.xml"
    blog_urls = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        try:
            # Get the first page to find total number of pages
            await page.goto(f"{base_url}/")
            await page.wait_for_selector("ul.page-numbers")

            html_content = await page.content()
            soup = BeautifulSoup(html_content, "html.parser")
            pagination = soup.select("ul.page-numbers li")

            if not pagination:
                raise ValueError("Could not find pagination")

            # Get the last page number
            last_page = int(pagination[-2].get_text().strip())

            for page_num in range(1, last_page + 1):
                print(f"Processing page {page_num} of {last_page}")
                page_url = (
                    f"{base_url}/page/{page_num}/" if page_num > 1 else f"{base_url}/"
                )

                await page.goto(page_url)
                await page.wait_for_selector("div.post-box")

                html_content = await page.content()
                soup = BeautifulSoup(html_content, "html.parser")
                post_boxes = soup.select("div.post-box > a")

                for post_box in post_boxes:
                    post_url = post_box.get("href")
                    if post_url:
                        blog_urls.append(post_url)

        except Exception as e:
            print(f"An error occurred while crawling: {e}")

        finally:
            await browser.close()

    print(f"Found {len(blog_urls)} blog post URLs")
    with open("blog_urls.txt", "w") as f:
        f.write("\n".join(blog_urls))
    return blog_urls


async def process_blog_posts(blog_urls) -> AsyncGenerator[BlogPost, None]:
    llm = ChatOpenAI(temperature=0, model="gpt-4o-mini")
    llm_with_structured_output = llm.with_structured_output(BlogPost)

    system_prompt = """You are a blog post content extraction assistant. Your task is to process the provided cleaned text of a blog post and extract structured information according to the schema described below. Your output must be valid JSON and follow the schema exactly without any additional commentary or markdown formatting.

    KEEP EVERYTHING IN PERSIAN LANGUAGE.
    DO NOT ADD ANY ADDITIONAL TEXT OR COMMENTS TO THE OUTPUT.
    
    Now, process the following cleaned text:
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        for url in blog_urls:
            try:
                await page.goto(url)
                await page.wait_for_load_state("networkidle")

                html_content = await page.content()
                cleaned_content = clean_html(html_content)

                # Process with LLM
                blog_post = llm_with_structured_output.invoke(
                    f"{system_prompt}\nCleaned Text:\n{cleaned_content}\nURL: {url}"
                )

                yield blog_post

            except Exception as e:
                print(f"An error occurred while processing blog post: {e}")

        await browser.close()


async def crawl_and_process_blog_posts() -> None:
    """
    End-to-end function that:
    1. Crawls blog URLs from tahagasht.com
    2. Processes each blog post to extract structured content
    3. Stores the processed content in a vector database
    """
    vectorstore = VectorStoreHandler()
    try:
        # Step 1: Get all blog URLs
        print("Starting to crawl blog URLs...")
        blog_urls = await crawl_blog_urls(use_cached=True)
        print(f"Found {len(blog_urls)} blog URLs")

        print("Filtering already existing URLs...")
        blog_urls = [
            url
            for url in blog_urls
            if not await vectorstore.url_exists_in_vectorstore(url)
        ]
        print(f"Found {len(blog_urls)} new blog URLs")

        # Step 2: Process blog posts to extract structured content
        print("\nProcessing blog posts...")
        i = 0
        async for post in process_blog_posts(blog_urls):
            try:
                # Step 3: Store the structured content in the vectorstore
                ids = await vectorstore.process_and_store_blog_posts([post])
                print(f"Processed blog post {i + 1}({len(ids)}): {post.url}")
                i += 1
            except Exception as e:
                print(f"An error occurred while processing blog post: {e}\n{post}")

        print(f"Successfully processed {len(blog_urls)} blog posts")

        return vectorstore

    except Exception as e:
        print(f"An error occurred during the crawl and process pipeline: {e}")
        raise
