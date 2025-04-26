# 🤖 AI Article Generator

A powerful web application that generates high-quality AI-focused articles using Google's Gemini AI. Built with FastAPI and modern web technologies.

## ✨ Features

### Article Generation
- 🎯 Topic-based article generation
- 📝 Customizable content structure
- 🎨 Adjustable writing tone and style
- 📊 Multiple content sections including:
  - Introduction and Overview
  - Key Concepts and Definitions
  - Technical Architecture
  - Implementation Approaches
  - Practical Applications
  - Future Trends
  - FAQ Section

### Customization Options
- 🎭 Adjustable tone (professional, casual, technical)
- 👥 Target audience selection
- 📈 Complexity level control
- 📏 Custom word count targets
- 🌐 Language selection

### Advanced Features
- 💻 Code snippet integration
- 📊 Mermaid diagram support
- 📚 Reference management
- 📑 Table of contents generation
- ❓ FAQ section generation
- 🎯 SEO optimization

### Analytics
- 📊 Detailed content metrics
- ⏱️ Reading time estimation
- 📈 Content quality scores
- 🔍 SEO analysis
- 📱 Engagement metrics

## 🛠️ Technologies Used

- **Backend**: FastAPI
- **AI Model**: Google Gemini AI
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript
- **Documentation**: OpenAPI/Swagger

## 🚀 Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Harsha2318/AI_AGENT_ARTICLE.git
   cd AI_AGENT_ARTICLE
   ```

2. **Create and activate virtual environment**:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Create a `.env` file in the project root
   - Add your Gemini API key:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```
   - Get your API key from: https://makersuite.google.com/app/apikey

5. **Run the application**:
   ```bash
   python app.py
   ```

6. **Access the application**:
   - Open your browser and navigate to `http://localhost:8000`
   - API documentation available at `http://localhost:8000/docs`
   - Alternative API docs at `http://localhost:8000/redoc`

## 📁 Project Structure

```
AI_AGENT_ARTICLE/
├── app.py              # Main FastAPI application
├── requirements.txt    # Project dependencies
├── templates/         # HTML templates
│   └── index.html    # Main application template
├── static/           # Static assets (CSS, JS, images)
├── .env              # Environment variables
├── .gitignore        # Git ignore rules
└── README.md         # Project documentation
```

## 🔧 API Endpoints

- `GET /` - Web interface
- `POST /generate-article` - Generate new article
- `GET /articles` - List generated articles
- `GET /articles/{article_id}` - Get specific article

## 📊 Response Format

```json
{
  "id": 1,
  "article": "Generated article content in markdown",
  "metrics": {
    "content_metrics": {
      "word_count": 5000,
      "reading_time_minutes": 25,
      "structure_score": 0.8,
      "seo_score": 0.75
      // ... other metrics
    },
    "metadata": {
      "topic": "AI in Healthcare",
      "tone": "professional",
      "complexity": "medium"
      // ... other metadata
    }
  }
}
```

## 🤝 Contributing

Feel free to fork this repository and submit pull requests. For major changes:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

- **Harsha P**
- **Email**: harshagowda2318@gmail.com
- **GitHub**: [Harsha2318](https://github.com/Harsha2318)

## 🌟 Acknowledgments

- Google Gemini AI for the powerful language model
- FastAPI for the excellent web framework
- The open-source community for inspiration and tools
