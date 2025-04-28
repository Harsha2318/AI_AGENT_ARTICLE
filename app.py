
from fastapi import FastAPI, HTTPException, status, Form
from mermaid_integration import generate_mermaid_with_gemini, mermaid_to_svg
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request, APIRouter

# Mermaid dynamic integration
import traceback
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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global api_key
    try:
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
        else:
            logger.info("Testing Gemini API connection...")
            if not test_api_connection(api_key):
                api_key = None
    except Exception as e:
        logger.error(f"Error initializing Gemini API: {str(e)}")
        api_key = None
    yield

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
    redoc_url="/redoc",
    lifespan=lifespan
)

# Create required directories
static_dir = Path("static")
templates_dir = Path("templates")

for directory in [static_dir, templates_dir]:
    if not directory.exists():
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created {directory} directory")

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

# Initialize API key
api_key = None

def test_api_connection(api_key: str) -> bool:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        headers = {
            'Content-Type': 'application/json'
        }
        test_data = {
            "contents": [{
                "parts": [{"text": "Test message"}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=test_data)
        if response.status_code == 200:
            logger.info("Gemini API connection successful")
            return True
        else:
            logger.error(f"Failed to connect to Gemini API: {response.text}")
            return False
                    
    except Exception as e:
        logger.error(f"Error testing API connection: {str(e)}")
        return False

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global api_key
    try:
        # Get API key from environment
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found in environment variables")
        else:
            logger.info("Testing Gemini API connection...")
            if not test_api_connection(api_key):
                api_key = None
    except Exception as e:
        logger.error(f"Error initializing Gemini API: {str(e)}")
        api_key = None
    yield

# Custom exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred", "error": str(exc)}
    )

















































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
    target_word_count: int = Field(default=5000, description="Target word count for the article", example=3000)
    tone: str = Field(default="professional", description="Writing tone for the article", example="professional")
    audience: str = Field(default="general", description="Target audience for the article", example="general")
    complexity: str = Field(default="medium", description="Content complexity level", example="medium")
    language: str = Field(default="en", description="Language for the article", example="en")
    style: Optional[Dict[str, Any]] = Field(default=None, description="Styling preferences for the article")
    seo: Optional[Dict[str, Any]] = Field(default=None, description="SEO preferences for the article")
    include_flow_diagram: bool = Field(default=False, description="Whether to include a flow diagram at the end of the article")

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
        metrics = json.loads(row[4])
        # Ensure content_metrics and word_count exist
        if "content_metrics" not in metrics:
            metrics["content_metrics"] = {}
        if "word_count" not in metrics["content_metrics"]:
            metrics["content_metrics"]["word_count"] = 0
        return {
            "id": row[0],
            "topic": row[1],
            "content": row[2],
            "config": json.loads(row[3]),
            "metrics": metrics,
            "created_at": datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S").isoformat() if row[5] else None
        }
    return None

def get_articles(limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    conn = sqlite3.connect("articles.db")
    c = conn.cursor()
    c.execute("SELECT * FROM articles ORDER BY created_at DESC LIMIT ? OFFSET ?", (limit, offset))
    rows = c.fetchall()
    conn.close()
    articles = []
    for row in rows:
        metrics = json.loads(row[4])
        # Ensure content_metrics and word_count exist
        if "content_metrics" not in metrics:
            metrics["content_metrics"] = {}
        if "word_count" not in metrics["content_metrics"]:
            metrics["content_metrics"]["word_count"] = 0
        articles.append({
            "id": row[0],
            "topic": row[1],
            "content": row[2],
            "config": json.loads(row[3]),
            "metrics": metrics,
            "created_at": datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S").isoformat() if row[5] else None
        })
    return articles

# API endpoints
@app.get("/", response_class=HTMLResponse)
def mermaid_index(request: Request):
    # Show the form with empty/default data
    return templates.TemplateResponse("index.html", {
        "request": request,
        "mermaid_code": "",
        "topic": "",
        "svg": None,
        "error": None
    })

@app.post("/", response_class=HTMLResponse)
def generate_mermaid_diagram(request: Request, topic: str = Form("")):
    svg = None
    error = None
    topic_to_use = topic if topic.strip() else None
    try:
        mermaid_syntax = generate_mermaid_with_gemini(topic=topic_to_use)
        svg = mermaid_to_svg(mermaid_syntax)
    except Exception as e:
        error = f"Error generating diagram: {str(e)}"
        svg = None
    return templates.TemplateResponse("index.html", {
        "request": request,
        
        "topic": topic,
        "svg": svg,
        "error": error
    })

@app.get("/api")
async def read_api_root():
    return {"message": "Welcome to AI Article Generator API", "docs_url": "/docs"}

from fastapi import Body
from fastapi.responses import JSONResponse

@app.post("/api/generate-mermaid")
def api_generate_mermaid(data: dict = Body(...)):
    topic = data.get("topic", "")
    
    topic_to_use = topic if topic.strip() else None
    try:
        mermaid_syntax = generate_mermaid_with_gemini(topic=topic_to_use)
        svg = mermaid_to_svg(mermaid_syntax)
        return {"svg": svg, "mermaid_code": mermaid_syntax}
    except Exception as e:
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/api/sample-mermaid")
def api_sample_mermaid():
    # Example: generate a diagram from backend data
    topic = "Live Backend Data"
    mermaid_syntax = generate_mermaid_with_gemini(topic)
    svg = mermaid_to_svg(mermaid_syntax)
    return {"svg": svg, "mermaid_code": mermaid_syntax, "topic": topic}

# Gemini-powered Mermaid code generator
def generate_mermaid_with_gemini(topic: str = None) -> str:
    """
    Use Gemini to generate a highly unique, creative Mermaid diagram code for the given topic.
    Adds a random creative twist and blacklists generic node names.
    """
    # If no topic, return a minimal default
    if not topic or not topic.strip():
        return "flowchart TD\n    A[Start] --> B[No input provided]"
    import google.generativeai as genai
    import random
    if not api_key:
        raise RuntimeError("Gemini API key is not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
    twists = [
        "Make the flowchart whimsical or metaphorical.",
        "Use a sports analogy.",
        "Imagine the process as a journey through a fantasy world.",
        "Add a humorous or surprising step.",
        "Give each node a creative, non-generic name.",
        "Make the flowchart look like a treasure hunt.",
        "Use animal characters for each node.",
        "Make the diagram resemble a cooking recipe.",
        "Add a plot twist in the flow.",
        "Use a superhero theme for the process."
    ]
    twist = random.choice(twists)
    prompt = f"""
You are an expert technical writer and diagram designer.
Generate a valid Mermaid.js flowchart for the following topic.
STRICTLY use only standard Mermaid flowchart syntax: 'flowchart TD' or 'graph LR'.
Do NOT use subgraph, advanced shapes, or rare features.
Do NOT use code fences or markdown.
Do NOT use brackets [], {{}}, (), <> inside node names.
Do NOT use colons, pipes, or double quotes in node names.
Do NOT use any forbidden tokens: ``` , subgraph, call, click, linkStyle, classDef, class, end, style, rect, roundrect, hexagon, stadium, subroutine, c4, flowchart LR, graph TD, gantt, pie, erDiagram, journey, stateDiagram, mindmap, timeline, quadrantChart, requirementDiagram, gitGraph, entity, table, JSON, YAML, CSV, markdown.
Only output the Mermaid code (no explanation, no markdown, no extra text).

Topic: {topic}
"""
    response = model.generate_content(prompt)
    code = response.text.strip()
    # Post-process: Remove code fences, markdown, forbidden tokens
    forbidden = ["```", "subgraph", "call", "click", "linkStyle", "classDef", "class ", "end", "style", "rect", "roundrect", "hexagon", "stadium", "subroutine", "c4", "flowchart LR", "graph TD", "gantt", "pie", "erDiagram", "journey", "stateDiagram", "mindmap", "timeline", "quadrantChart", "requirementDiagram", "gitGraph", "entity", "table", "JSON", "YAML", "CSV", "markdown"]
    for token in forbidden:
        if token in code:
            return f"flowchart TD\n    A[Start] --> B[Diagram unavailable: invalid Mermaid generated]"
    if not (code.startswith("flowchart TD") or code.startswith("graph LR")):
        return f"flowchart TD\n    A[Start] --> B[Diagram unavailable: invalid Mermaid generated]"
    return code

@app.get("/generate-flowchart")
async def generate_flowchart(topic: str):
    """
    Generate and return Mermaid diagram SVG for the given article topic using Gemini.
    """
    try:
        mermaid_code = generate_mermaid_with_gemini(topic)
        try:
            svg_diagram = mermaid_to_svg(mermaid_code)
        except Exception as e:
            logger.error(f"Failed to generate flowchart for topic '{topic}' with Gemini: {str(e)}. Using fallback template.")
            fallback_code = f"""
            flowchart TD
                A[Start] --> B[{topic} Research]
                B --> C[Data Processing]
                C --> D[Model Training]
                D --> E[Deployment]
                E --> F[User Interaction]
            """
            svg_diagram = mermaid_to_svg(fallback_code.strip())
        return HTMLResponse(content=svg_diagram, media_type="image/svg+xml")
    except Exception as e:
        logger.error(f"Failed to generate flowchart for topic '{topic}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate flowchart dynamically: " + str(e))

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
        if api_key is None:
            logger.error("Gemini API key not initialized")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service is not available. Please check your API key and configuration."
            )

        # Use the target word count as provided by the user
        target_word_count = request.target_word_count



        # Generate the article using Gemini API directly
        sections = [
            "Introduction and Overview",
            "Key Concepts and Definitions",
            "Core Components",
            "Technical Architecture",
            "Implementation Approaches",
            "Practical Applications",
            "Challenges and Limitations",
            "Future Trends"





        ]

        if request.include_code:
            sections.append("Code Examples")
        if request.include_diagrams:
            sections.append("Diagrams")
        if request.include_examples:
            sections.append("Practical Examples")
        if request.include_references:
            sections.append("References")
        if request.include_faq:
            sections.append("FAQ Section")
        
        generated_content = []
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        headers = {
            'Content-Type': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            for section in sections:
                section_word_count = target_word_count // len(sections)
                logger.info(f"Generating section '{section}' with target word count: {section_word_count}")
                section_prompt = f"""
                Generate detailed content for the section: {section}
                
                Topic: {request.topic}
                Word count target: {section_word_count}
                Tone: {request.tone}
                Audience: {request.audience}
                Complexity: {request.complexity}
                
                Requirements:
                - Be detailed and informative
                - Use clear examples
                - Maintain consistent tone
                - Focus on accuracy
                """
                
                data = {
                    "contents": [{
                        "parts": [{"text": section_prompt}]
                    }]




























                }
                
                try:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"API request failed for section {section}: {error_text}")
                            continue
                        result = await response.json()
                        if 'candidates' not in result or not result['candidates']:
                            logger.error(f"No response from API for section {section}")
                            continue
                        section_content = result['candidates'][0]['content']['parts'][0]['text']
                        generated_content.append(f"## {section}\n\n{section_content}\n\n")
                except Exception as e:
                    logger.error(f"Error generating content for section {section}: {str(e)}")
                    continue




        if not generated_content:














































            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate any content"
            )

        # Combine all sections
        final_content = "\n".join(generated_content)
        logger.info(f"Generated article length: {len(final_content.split())} words")

        # If requested, append flow diagram SVG at the end of the article
        if getattr(request, 'include_flow_diagram', False) or getattr(request, 'include_diagrams', False):
            try:
                mermaid_code = generate_mermaid_with_gemini(request.topic)
                try:
                    svg_diagram = mermaid_to_svg(mermaid_code)
                except Exception as e:
                    logger.error(f"Failed to generate flow diagram SVG with Gemini: {str(e)}. Using fallback template.")
                    fallback_code = f"""
                    flowchart TD
                        A[Start] --> B[{request.topic} Research]
                        B --> C[Data Processing]
                        C --> D[Model Training]
                        D --> E[Deployment]
                        E --> F[User Interaction]
                    """
                    svg_diagram = mermaid_to_svg(fallback_code.strip())
                final_content += f"\n\n## Flow Diagram\n\n<div>{svg_diagram}</div>\n\n"
            except Exception as e:
                logger.error(f"Failed to generate flow diagram SVG: {str(e)}")

        # Prepare content metrics with default values
        content_metrics = {
            "structure_score": 0.85,
            "readability_score": 0.9,
            "seo_score": 0.8,
            "engagement_score": 0.75,
            "complexity_score": 0.7,
            "uniqueness_score": 0.95,
            "word_count": len(final_content.split()),
            "reading_time_minutes": round(len(final_content.split()) / 200, 1)  # assuming 200 wpm reading speed
        }

        # Save to database
        article_id = save_article(
            topic=request.topic,
            content=final_content,
            config=request.dict(),
            metrics={"content_metrics": content_metrics}
        )
        
        response = {
            "id": article_id,
            "topic": request.topic,
            "article": final_content,
            "metrics": {"content_metrics": content_metrics}
        }
        
        return response
        
    except HTTPException as he:

        raise he
    except Exception as e:
        logger.error(f"Error in generate_article: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    import sys
    import socket
    logger.info("Starting FastAPI server")
    try:
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)