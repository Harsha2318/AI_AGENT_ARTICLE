import os
from dotenv import load_dotenv
load_dotenv()

import serpapi
import time
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
# from serpapi import GoogleSearch
from serpapi.google_search import GoogleSearch
import pandas as pd
import re
from concurrent.futures import ThreadPoolExecutor

class AIArticleAgent:
    def __init__(self, gemini_api_key, serpapi_key):
        """Initialize the AI Article Agent with necessary API keys"""
        self.serpapi_key = serpapi_key
        
        # Set up Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        
        # Store brand voice profile
        self.brand_voice_profile = None
        
        # Store internal link database
        self.internal_links = {}
        
        print("Gemini API Key:", gemini_api_key)  # Debug line

    def _generate_content_with_retry(self, prompt, max_retries=5, initial_delay=5):
        """Helper method to call generate_content with retry on quota errors"""
        import time
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                return response
            except Exception as e:
                # Check if error is quota exceeded
                if "ResourceExhausted" in str(e) or "429" in str(e):
                    print(f"Quota exceeded, retrying in {delay} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff
                else:
                    # Other errors, raise immediately
                    raise
        raise Exception(f"Failed to generate content after {max_retries} retries due to quota limits.")

    
    def train_on_brand_voice(self, brand_content_urls=None, brand_content_text=None):
        """Analyze brand content to extract voice and style patterns"""
        brand_samples = []
        
        # Collect content from provided URLs
        if brand_content_urls:
            for url in brand_content_urls:
                try:
                    content = self._scrape_content(url)
                    if content:
                        brand_samples.append(content)
                except Exception as e:
                    print(f"Error processing {url}: {e}")
        
        # Add directly provided text samples
        if brand_content_text:
            if isinstance(brand_content_text, list):
                brand_samples.extend(brand_content_text)
            else:
                brand_samples.append(brand_content_text)
        
        # Ensure we have content to analyze
        if not brand_samples:
            raise ValueError("No brand content provided for voice training")
        
        # Combine samples and prepare for analysis
        combined_samples = "\n\n".join(brand_samples)
        
        # Create analysis prompt
        voice_analysis_prompt = f"""
        Analyze the following brand content and extract detailed stylistic elements:
        
        1. Tone characteristics:
           - Formal vs casual balance
           - Emotional tone (enthusiastic, authoritative, friendly, etc.)
           - Use of humor or wit
        
        2. Sentence structures:
           - Average sentence length
           - Complexity patterns
           - Question frequency
           - Command/imperative use
        
        3. Vocabulary preferences:
           - Word choice patterns
           - Industry jargon usage
           - Language complexity
        
        4. Rhetorical devices:
           - Metaphor/analogy usage
           - Repetition patterns
           - Persuasive techniques
        
        5. Content organization:
           - Introduction approaches
           - Transition styles
           - Conclusion patterns
        
        6. Content attributes:
           - First/second/third person usage
           - Active vs passive voice preference
           - Contractions and informal language
        
        Content for analysis:
        {combined_samples[:15000]}  # Limiting size for API constraints
        
        Provide a comprehensive style guide that can be used to replicate this brand voice.
        """
        
        response = self._generate_content_with_retry(voice_analysis_prompt)
        self.brand_voice_profile = response.text
        
        # Build database of internal links
        if brand_content_urls:
            self._build_internal_link_database(brand_content_urls)
        
        return self.brand_voice_profile
    
    def _build_internal_link_database(self, urls):
        """Extract topics and URLs to create internal linking opportunities"""
        for url in urls:
            try:
                content = self._scrape_content(url)
                soup = BeautifulSoup(requests.get(url).text, 'html.parser')
                
                # Extract title and main keywords
                title = soup.find('title').text if soup.find('title') else ""
                h1 = soup.find('h1').text if soup.find('h1') else ""
                
                # Extract meta keywords and description
                meta_keywords = ""
                meta_desc = ""
                for meta in soup.find_all('meta'):
                    if meta.get('name', '').lower() == 'keywords':
                        meta_keywords = meta.get('content', '')
                    elif meta.get('name', '').lower() == 'description':
                        meta_desc = meta.get('content', '')
                
                # Store in database with core topic keywords
                key_terms = self._extract_key_terms(f"{title} {h1} {meta_keywords} {meta_desc}")
                
                for term in key_terms:
                    if term not in self.internal_links:
                        self.internal_links[term] = []
                    
                    if url not in self.internal_links[term]:
                        self.internal_links[term].append({
                            'url': url,
                            'title': title,
                            'relevance': key_terms[term]
                        })
            
            except Exception as e:
                print(f"Error building internal link database for {url}: {e}")
    
    def _extract_key_terms(self, text):
        """Extract potential keywords from text with relevance scores"""
        # This is a simplified approach - in production, use NLP or keyword extraction API
        words = re.findall(r'\b[a-zA-Z]{3,15}\b', text.lower())
        word_counts = {}
        
        for word in words:
            if word not in ['and', 'the', 'for', 'with', 'that', 'this', 'from', 'your']:
                word_counts[word] = word_counts.get(word, 0) + 1
        
        # Find multi-word phrases (simplified approach)
        phrases = re.findall(r'\b[a-zA-Z]{3,15} [a-zA-Z]{3,15}\b', text.lower())
        for phrase in phrases:
            if not any(stop in phrase for stop in ['and the', 'for the', 'with the']):
                word_counts[phrase] = word_counts.get(phrase, 0) + 3  # Weight phrases higher
        
        # Normalize scores from 0-1
        if word_counts:
            max_count = max(word_counts.values())
            return {word: count/max_count for word, count in word_counts.items()}
        return {}
    
    def _scrape_content(self, url):
        """Scrape and extract main content from a URL"""
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract article content (simplified approach)
            article = soup.find('article')
            if article:
                content = article.get_text(separator='\n')
            else:
                # Fallback to main content area extraction
                content_elements = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'])
                content = '\n'.join([el.get_text() for el in content_elements])
            
            return content
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def research_topic(self, topic, primary_keyword, secondary_keywords=None, num_results=10):
        """Research a topic by analyzing SERPs and top-ranking content"""
        if secondary_keywords is None:
            secondary_keywords = []
        
        # SERP analysis
        search_query = f"{primary_keyword} {topic}"
        params = {
            "engine": "google",
            "q": search_query,
            "api_key": self.serpapi_key,
            "num": num_results
        }
        
        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract ranking URLs 
            top_urls = [result['link'] for result in results.get('organic_results', [])[:num_results]]
            
            # Extract "People also ask" questions
            paa_questions = []
            if 'related_questions' in results:
                paa_questions = [item['question'] for item in results['related_questions']]
            
            # Analyze competitor content in parallel
            with ThreadPoolExecutor(max_workers=5) as executor:
                content_analyses = list(executor.map(self._analyze_competitor_content, top_urls))
            
            # Filter out failed scrapes
            content_analyses = [ca for ca in content_analyses if ca and 'error' not in ca]
            
            # Find expert quotes across all content
            all_quotes = []
            for analysis in content_analyses:
                if 'quotes' in analysis:
                    all_quotes.extend(analysis['quotes'])
            
            # Determine optimal content structure based on top performers
            optimal_structure = self._determine_optimal_structure(content_analyses)
            
            # Find potentially useful statistics and facts
            key_facts = self._extract_key_facts(content_analyses)
            
            return {
                "serp_features": {
                    "paa_questions": paa_questions,
                    "featured_snippets": results.get('answer_box', {}),
                },
                "competitor_analysis": content_analyses,
                "expert_quotes": all_quotes[:10],  # Limit to top 10 most relevant quotes
                "optimal_structure": optimal_structure,
                "key_facts": key_facts,
                "avg_word_count": sum(a.get('word_count', 0) for a in content_analyses) // len(content_analyses) if content_analyses else 0
            }
            
        except Exception as e:
            print(f"Error researching topic: {e}")
            return None
    
    def _analyze_competitor_content(self, url):
        """Analyze a competitor's article for structure, quotes, word count, etc."""
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract content
            title = soup.find('title').text if soup.find('title') else ""
            
            # Get headings and create structural outline
            headings = []
            for tag in ['h1', 'h2', 'h3', 'h4']:
                for heading in soup.find_all(tag):
                    headings.append({
                        'level': int(tag[1]),
                        'text': heading.get_text().strip()
                    })
            
            # Get all paragraphs
            paragraphs = [p.get_text().strip() for p in soup.find_all('p') if len(p.get_text().strip()) > 20]
            word_count = sum(len(p.split()) for p in paragraphs)
            
            # Extract potential quotes (paragraphs with quotation marks or attribution patterns)
            quotes = []
            quote_patterns = [
                r'"[^"]{10,500}"',  # Regular quotes
                r'"[^"]{10,500}"',  # Smart quotes
                r'according to [^.,]{3,50}',  # Attribution
                r'said [^.,]{3,50}',  # Said attribution
                r'says [^.,]{3,50}'   # Says attribution
            ]
            
            for p in paragraphs:
                for pattern in quote_patterns:
                    matches = re.findall(pattern, p, re.IGNORECASE)
                    for match in matches:
                        quotes.append(p)
                        break
                        
            # Extract potential key facts (sentences with numbers, statistics, years)
            facts = []
            fact_patterns = [
                r'\b\d{1,3}%',  # Percentage
                r'\b\d+\s+(?:million|billion|thousand)',  # Large numbers
                r'\bin \d{4}\b',  # Years
                r'\b(?:research|study|survey)(?:s)? (?:show|found|indicate)',  # Research findings
                r'\baccording to (?:research|a study|data)'  # Cited research
            ]
            
            for p in paragraphs:
                for pattern in fact_patterns:
                    if re.search(pattern, p, re.IGNORECASE):
                        facts.append(p)
                        break
            
            return {
                "url": url,
                "title": title,
                "structure": headings,
                "word_count": word_count,
                "quotes": list(set(quotes)),  # Remove duplicates
                "facts": list(set(facts)),
                "content_sample": " ".join(paragraphs[:5])  # Sample of content for analysis
            }
            
        except Exception as e:
            print(f"Error analyzing {url}: {e}")
            return {"url": url, "error": str(e)}
    
    def _determine_optimal_structure(self, content_analyses):
        """Determine optimal content structure based on competitor analysis"""
        # Collect all headings
        all_headings = []
        for analysis in content_analyses:
            if 'structure' in analysis:
                all_headings.extend(analysis['structure'])
        
        if not all_headings:
            return []
            
        # Group similar headings
        heading_groups = {}
        for heading in all_headings:
            # Normalize heading text
            normalized = re.sub(r'[^a-zA-Z0-9\s]', '', heading['text'].lower())
            normalized = re.sub(r'\s+', ' ', normalized).strip()
            
            # Skip very short or empty headings
            if len(normalized) < 3:
                continue
                
            # Group by first 3 significant words to find similar headings
            key_words = [w for w in normalized.split() if w not in ['a', 'an', 'the', 'and', 'or', 'but', 'for', 'with']]
            group_key = ' '.join(key_words[:3]) if key_words else normalized
            
            if group_key not in heading_groups:
                heading_groups[group_key] = []
            heading_groups[group_key].append(heading)
        
        # Find most common heading patterns
        common_headings = []
        for group, headings in heading_groups.items():
            if len(headings) >= 2:  # At least appears in 2 competitor articles
                avg_level = sum(h['level'] for h in headings) / len(headings)
                common_headings.append({
                    'text': max(headings, key=lambda h: len(h['text']))['text'],  # Use the longest version
                    'level': round(avg_level),
                    'frequency': len(headings)
                })
        
        # Sort by heading level and then frequency
        common_headings.sort(key=lambda h: (h['level'], -h['frequency']))
        
        return common_headings
    
    def _extract_key_facts(self, content_analyses):
        """Extract statistically-rich sentences and facts from competitor content"""
        all_facts = []
        for analysis in content_analyses:
            if 'facts' in analysis:
                all_facts.extend(analysis['facts'])
        
        # Remove duplicates and near-duplicates
        unique_facts = []
        for fact in all_facts:
            # Check if this fact is significantly different from ones we've already kept
            if not any(self._text_similarity(fact, existing) > 0.7 for existing in unique_facts):
                unique_facts.append(fact)
        
        return unique_facts[:15]  # Limit to top 15 facts
    
    def _text_similarity(self, text1, text2):
        """Compute a simple similarity score between two text strings"""
        # This is a very basic implementation - consider using proper NLP for production
        words1 = set(re.findall(r'\b[a-zA-Z]{3,15}\b', text1.lower()))
        words2 = set(re.findall(r'\b[a-zA-Z]{3,15}\b', text2.lower()))
        
        if not words1 or not words2:
            return 0
            
        common_words = words1.intersection(words2)
        return len(common_words) / max(len(words1), len(words2))
    
    def _create_article_outline(self, topic, research_data, primary_keyword):
        """Generate an article outline based on research data and topic"""
        outline = f"# Article Outline for {topic}\n\n"
        
        # Use optimal_structure from research_data if available
        if research_data and 'optimal_structure' in research_data:
            for heading in research_data['optimal_structure']:
                level = heading.get('level', 2)
                text = heading.get('text', '')
                # Convert level to markdown heading (H2=##, H3=###, etc.)
                md_level = '#' * level
                outline += f"{md_level} {text}\n\n"
        else:
            # Fallback outline if no structure data
            outline += f"## Introduction\n\n## Main Content\n\n## Conclusion\n\n"
        
        return outline

    def generate_article(self, topic, research_data, primary_keyword, secondary_keywords=None, 
                         target_word_count=2000, include_faq=True):
        """Generate a complete SEO-optimized article using the research data"""
        if secondary_keywords is None:
            secondary_keywords = []
            
        # Prepare the outline based on research
        outline = self._create_article_outline(topic, research_data, primary_keyword)
        
        # Format keywords for the prompt
        keyword_str = f"Primary keyword: {primary_keyword}\n"
        if secondary_keywords:
            keyword_str += f"Secondary keywords: {', '.join(secondary_keywords)}\n"
        
        # Prepare expert quotes if available
        quote_examples = ""
        if research_data.get('expert_quotes'):
            quotes = research_data['expert_quotes'][:5]  # Limit to 5 quotes
            quote_examples = "Expert quotes to incorporate (use these exact quotes):\n" + \
                             "\n".join([f"- {quote}" for quote in quotes])
        
        # Prepare key facts if available
        facts_examples = ""
        if research_data.get('key_facts'):
            facts = research_data['key_facts'][:10]  # Limit to 10 facts
            facts_examples = "Key facts and statistics to incorporate (paraphrase appropriately):\n" + \
                             "\n".join([f"- {fact}" for fact in facts])
        
        # Add internal linking opportunities
        internal_linking = ""
        for kw in [primary_keyword] + secondary_keywords:
            for term in self.internal_links:
                if kw.lower() in term.lower() or term.lower() in kw.lower():
                    links = self.internal_links[term]
                    if links:
                        internal_linking += f"\nLink to relevant content: '{links[0]['title']}' at {links[0]['url']}"
        
        # Prepare FAQ section if needed
        faq_section = ""
        if include_faq and research_data.get('serp_features', {}).get('paa_questions'):
            questions = research_data['serp_features']['paa_questions'][:5]
            faq_section = "Include an FAQ section with these questions:\n" + \
                          "\n".join([f"- {q}" for q in questions])
        
        # Create the brand voice instructions
        brand_voice_instructions = ""
        if self.brand_voice_profile:
            brand_voice_instructions = f"""
IMPORTANT: Write in this exact brand voice style:
{self.brand_voice_profile}
"""
        
        # Create the full generation prompt
        prompt = f"""
You are an expert SEO content writer creating a comprehensive, factual, and engaging article on "{topic}".

{brand_voice_instructions}

CONTENT SPECIFICATIONS:
- Target word count: {target_word_count} words
- {keyword_str}
- Article should be substantive, informative, and factually accurate
- Use appropriate headings (H2, H3, H4) for structure
- Include a compelling introduction and conclusion
- Create content that answers user intent for the primary keyword

STRUCTURE TO FOLLOW:
{outline}

{quote_examples}

{facts_examples}

{internal_linking}

{faq_section}

IMPORTANT GUIDELINES:
1. Write in a natural, engaging way while organically incorporating keywords
2. Support claims with the facts and statistics provided
3. Include expert quotes where relevant (attribute properly)
4. Break up text with bulleted lists, examples, and subheadings where appropriate
5. Make the content genuinely helpful and comprehensive
6. Include a clear call-to-action in the conclusion
7. Format the article with proper Markdown

Please generate the complete article that follows these specifications.
"""
        
        try:
            # Generate content with Gemini
            response = self._generate_content_with_retry(prompt)
            article_content = response.text
            
            # Check if we need to expand the content to meet target word count
            current_word_count = len(article_content.split())
            if current_word_count < target_word_count * 0.8:
                # Generate additional content to expand shorter sections
                expansion_needed = target_word_count - current_word_count
                
                expansion_prompt = f"""
You previously wrote this article about "{topic}":

{article_content}

The article is currently {current_word_count} words, but needs to be expanded to reach {target_word_count} words.

Please identify 2-3 sections that could benefit from more depth, examples, or detail, and expand those sections only. 
Add approximately {expansion_needed} more words while maintaining the same brand voice and style.

Return the complete expanded article, not just the additions.
"""
                expansion_response = self._generate_content_with_retry(expansion_prompt)
                article_content = expansion_response.text
            return {
                "title": self._generate_seo_title(topic, primary_keyword),
                "content": article_content,
                "word_count": len(article_content.split()),
                "meta_description": self._generate_meta_description(article_content, primary_keyword)
            }
        except Exception as e:
            print(f"Error generating article: {e}")
            return None

    def _generate_seo_title(self, topic, primary_keyword):
        """Generate an SEO-friendly title for the article"""
        prompt = f"Generate a catchy and SEO-optimized title for an article about '{topic}' with primary keyword '{primary_keyword}'."
        try:
            response = self._generate_content_with_retry(prompt)
            title = response.text.strip().strip('"').strip("'")
            return title
        except Exception as e:
            print(f"Error generating SEO title: {e}")
            return f"{topic} - {primary_keyword}"

    def _generate_meta_description(self, article_content, primary_keyword):
        """Generate a meta description for the article"""
        prompt = f"Write a concise and compelling meta description for an article about '{primary_keyword}'. The article content is:\n{article_content[:500]}"
        try:
            response = self._generate_content_with_retry(prompt)
            description = response.text.strip().replace('\n', ' ')
            return description
        except Exception as e:
            print(f"Error generating meta description: {e}")
            return f"An article about {primary_keyword}."
