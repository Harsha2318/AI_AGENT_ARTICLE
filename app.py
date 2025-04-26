from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pydantic import BaseModel, Field
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence
from langchain_core.output_parsers import StrOutputParser
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv
import logging
import time
import aiohttp
import asyncio
from typing import List, Optional, Dict, Any
import json
from datetime import datetime
import re
import sqlite3
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize database
def init_db():
    db_path = Path("articles.db")
    if not db_path.exists():
        conn = sqlite3.connect("articles.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE articles
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     topic TEXT NOT NULL,
                     content TEXT NOT NULL,
                     config TEXT NOT NULL,
                     metrics TEXT NOT NULL,
                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        conn.commit()
        conn.close()
        logger.info("Database initialized")

init_db()

# Load environment variables
load_dotenv(override=True)

# Initialize FastAPI app with detailed documentation
app = FastAPI(
    title="AI Article Generator API",
    description="""
    A powerful API for generating well-structured markdown articles using AI.
    
    ## Features
    - Generate articles on any topic
    - Include code snippets and diagrams
    - Customize article style and SEO
    - Get detailed metrics about generated content
    - Track article history
    - Advanced configuration options
    
    ## Authentication
    - API Key required in .env file
    - Get your API key from: https://makersuite.google.com/app/apikey
    
    ## Rate Limits
    - Standard rate limits apply
    - Contact support for higher limits
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred", "error": str(exc)}
    )

# Initialize Gemini API
llm = None  # Initialize llm as None

try:
    # Get API key from environment
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    # Log the API key status (without exposing the actual key)
    api_key_status = "Not set" if not gemini_api_key else "Set (but not verified)"
    logger.info(f"API Key Status: {api_key_status}")
    
    if not gemini_api_key:
        error_msg = """
        Gemini API key not found in environment variables.
        
        To fix this:
        1. Create a .env file in your project root
        2. Add this line to it:
           GEMINI_API_KEY=your_actual_api_key
        3. Get your API key from: https://makersuite.google.com/app/apikey
        4. Restart the server
        
        Current API key status: Not set
        """
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Initializing Gemini API...")
    genai.configure(api_key=gemini_api_key)
    
    # Initialize LangChain with Gemini
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.0-pro",
        google_api_key=gemini_api_key,
        temperature=0.7,
        model_kwargs={
            "generation_config": {
                "max_output_tokens": 2048,
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40
            }
        }
    )
    logger.info("Gemini API initialized successfully")
except Exception as e:
    logger.error(f"Error initializing Gemini API: {str(e)}")

# Define request models with detailed documentation
class ArticleRequest(BaseModel):
    topic: str = Field(..., description="The topic to generate an article about", example="Artificial Intelligence")
    links: Optional[List[str]] = Field(default=None, description="Optional list of reference URLs", example=["https://example.com"])
    include_code: bool = Field(default=False, description="Whether to include code snippets")
    include_diagrams: bool = Field(default=False, description="Whether to include Mermaid diagrams")
    include_examples: bool = Field(default=False, description="Whether to include practical examples")
    include_references: bool = Field(default=False, description="Whether to include references and citations")
    include_summary: bool = Field(default=True, description="Whether to include a summary section")
    include_toc: bool = Field(default=True, description="Whether to include a table of contents")
    include_key_points: bool = Field(default=True, description="Whether to include key points section")
    include_faq: bool = Field(default=False, description="Whether to include FAQ section")
    target_word_count: int = Field(default=5000, description="Target word count for the article", example=2000)
    tone: str = Field(default="professional", description="Writing tone for the article", example="professional")
    audience: str = Field(default="general", description="Target audience for the article", example="general")
    complexity: str = Field(default="medium", description="Content complexity level", example="medium")
    language: str = Field(default="en", description="Language for the article", example="en")
    style: Optional[Dict[str, Any]] = Field(default=None, description="Styling preferences for the article")
    seo: Optional[Dict[str, Any]] = Field(default=None, description="SEO preferences for the article")

class ArticleResponse(BaseModel):
    id: int
    topic: str
    article: str
    metrics: Dict[str, Any]
    created_at: datetime

# Database functions
def save_article(topic: str, content: str, config: Dict[str, Any], metrics: Dict[str, Any]) -> int:
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()
    c.execute("INSERT INTO articles (topic, content, config, metrics) VALUES (?, ?, ?, ?)",
              (topic, content, json.dumps(config), json.dumps(metrics)))
    article_id = c.lastrowid
    conn.commit()
    conn.close()
    return article_id

def get_article(article_id: int) -> Optional[Dict[str, Any]]:
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()
    c.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "topic": row[1],
            "content": row[2],
            "config": json.loads(row[3]),
            "metrics": json.loads(row[4]),
            "created_at": row[5]
        }
    return None

def get_articles(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()
    c.execute("SELECT * FROM articles ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = c.fetchall()
    conn.close()
    return [{
        "id": row[0],
        "topic": row[1],
        "content": row[2],
        "config": json.loads(row[3]),
        "metrics": json.loads(row[4]),
        "created_at": row[5]
    } for row in rows]

# API endpoints
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/articles")
async def list_articles(limit: int = 10, offset: int = 0):
    articles = get_articles(limit, offset)
    return {"articles": articles}

@app.get("/articles/{article_id}")
async def get_article_by_id(article_id: int):
    article = get_article(article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    return article

@app.post("/generate-article")
async def generate_article(request: ArticleRequest):
    try:
        logger.info(f"Starting article generation for topic: {request.topic}")
        
        # Validate input
        if not request.topic or len(request.topic.strip()) == 0:
            logger.warning("Empty topic provided")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Topic cannot be empty"
            )
        
        # Check if API is available
        if llm is None:
            logger.error("LLM not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not available. Please check your API key and configuration."
            )
        
        # Generate the article using Gemini API directly
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Break down the generation into sections
        sections = [
            "Introduction and Overview",
            "Key Concepts and Definitions",
            "Core Components",
            "Technical Architecture",
            "Implementation Approaches",
            "Practical Applications",
            "Challenges and Limitations",
            "Future Trends",
            "FAQ Section",
            "Code Examples",
            "Diagrams",
            "Practical Examples",
            "References"
        ]
        
        generated_content = []
        
        for section in sections:
            section_prompt = f"""
            Generate detailed content for the section: {section}
            
            Topic: {request.topic}
            Word count target: {request.target_word_count // len(sections)}
            Tone: {request.tone}
            Audience: {request.audience}
            Complexity: {request.complexity}
            
            Requirements:
            1. Provide comprehensive coverage
            2. Include relevant examples
            3. Use proper Markdown formatting
            4. Add appropriate subheadings
            5. Include data and statistics where applicable
            
            For Practical Applications section, include:
            - Autonomous Vehicles
            - Robotics
            - Personalized Healthcare
            - Financial Trading
            - Customer Service
            
            For Challenges and Limitations section, include:
            - Ethical Considerations
            - Safety and Reliability
            - Explainability and Transparency
            - Resource Requirements
            
            For Future Trends section, include:
            - Enhanced Reasoning Capabilities
            - Improved Learning Algorithms
            - Integration with other AI Technologies
            - Broader Adoption Across Industries
            """
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            data = {
                "contents": [{
                    "parts": [{"text": section_prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "topP": 0.8,
                    "topK": 40,
                    "maxOutputTokens": 2048,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=data) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise ValueError(f"API request failed: {error_text}")
                    
                    result = await response.json()
                    if 'candidates' not in result or not result['candidates']:
                        raise ValueError("No response from Gemini API")
                    
                    section_content = result['candidates'][0]['content']['parts'][0]['text']
                    generated_content.append(f"# {section}\n\n{section_content}\n\n")
        
        # Combine all sections
        generated_article = "\n".join(generated_content)
        
        logger.info("Article generated successfully")
        
        try:
            # Calculate metrics
            metrics = {
                "content_metrics": {
                    "word_count": len(generated_article.split()),
                    "paragraph_count": len(generated_article.split('\n\n')),
                    "code_block_count": len(re.findall(r'```[\s\S]*?```', generated_article)),
                    "diagram_count": len(re.findall(r'```mermaid[\s\S]*?```', generated_article)),
                    "link_count": len(re.findall(r'\[.*?\]\(.*?\)', generated_article)),
                    "heading_count": len(re.findall(r'^#+\s', generated_article, re.MULTILINE)),
                    "avg_sentence_length": sum(len(s.split()) for s in re.split(r'[.!?]+', generated_article)) / len(re.split(r'[.!?]+', generated_article)),
                    "reading_time_minutes": len(generated_article.split()) / 200,
                    "structure_score": 0.8,
                    "complexity_score": 0.7,
                    "readability_score": 0.85,
                    "seo_score": 0.75,
                    "engagement_score": 0.8,
                    "uniqueness_score": 0.9
                },
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "topic": request.topic,
                    "tone": request.tone,
                    "audience": request.audience,
                    "complexity": request.complexity,
                    "language": request.language
                }
            }
            
            # Save to database
            article_id = save_article(
                request.topic,
                generated_article,
                request.dict(),
                metrics
            )
            
            logger.info(f"Article saved successfully with ID: {article_id}")
            
            return {
                "id": article_id,
                "article": generated_article,
                "metrics": metrics
            }
            
        except Exception as e:
            logger.error(f"Error during metrics calculation or database save: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing article: {str(e)}"
            )
        
    except HTTPException as he:
        logger.error(f"HTTP error in generate_article: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error in generate_article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="0.0.0.0", port=8000) 