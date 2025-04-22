import os
from ai_article_agent import AIArticleAgent

def main():
    # Initialize the AI article generation agent with necessary API keys
    agent = AIArticleAgent(
        gemini_api_key=os.environ.get("GEMINI_API_KEY"),
        serpapi_key=os.environ.get("SERPAPI_KEY")
    )
    
    print("Training on brand voice...")
    brand_urls = [
        "https://www.aiweekly.com/p/google-s-notebooklm-just-made-content-creation-10x-easier-youtube-to-blog-or-guide-in-minutes",
        "https://medium.com/aiguys/why-gen-ai-boom-is-fading-and-whats-next-7f1363b92696",
        "https://www.forbes.com/sites/bernardmarr/2023/10/02/the-top-5-ai-trends-in-2024/?sh=1f2a0c6b7d8e",
    ]
    # Train the agent using specified URLs to capture the brand's voice and style
    agent.train_on_brand_voice(brand_content_urls=brand_urls)
    print("Brand voice training complete!")
    
    
    # Step 2: Define your topic and keywords by user input
    topic = input("Enter the article topic: ").strip()
    primary_keyword = input("Enter the primary keyword: ").strip()
    secondary_keywords_input = input("Enter secondary keywords separated by commas: ").strip()
    secondary_keywords = [kw.strip() for kw in secondary_keywords_input.split(",") if kw.strip()]
    
    # Step 3: Research the topic
    print(f"Researching topic: {topic}...")
    research_data = agent.research_topic(
        topic=topic,
        primary_keyword=primary_keyword,
        secondary_keywords=secondary_keywords
    )
    print("Research complete!")
    
    # Step 4: Generate the article
    print("Generating article...")
    article = agent.generate_article(
        topic=topic,
        research_data=research_data,
        primary_keyword=primary_keyword,
        secondary_keywords=secondary_keywords,
        target_word_count=3000,
        include_faq=True
    )
    
    if article is None:
        print("Article generation failed. Please try again.")
        return
    
    # Step 5: Save the article
    with open(f"{topic.replace(' ', '_')}.md", "w", encoding="utf-8") as f:
        f.write(f"# {article['title']}\n\n")
        f.write(article['content'])
    
    print(f"Article successfully generated and saved!")
    print(f"Title: {article['title']}")
    print(f"Word count: {article['word_count']}")
    print(f"Meta description: {article['meta_description']}")

if __name__ == "__main__":
    main()