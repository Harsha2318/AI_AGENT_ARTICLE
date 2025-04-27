<div align="center">
  <img src="https://img.shields.io/github/stars/Harsha2318/AI_AGENT_ARTICLE?style=social" alt="Stars">
  <img src="https://img.shields.io/github/forks/Harsha2318/AI_AGENT_ARTICLE?style=social" alt="Forks">
  <img src="https://img.shields.io/github/issues/Harsha2318/AI_AGENT_ARTICLE" alt="Issues">
  <img src="https://img.shields.io/github/license/Harsha2318/AI_AGENT_ARTICLE" alt="License">
</div>

# 🧠 AI Article Generator

> **Generate beautiful, structured, and insightful articles with the power of AI and dynamic diagrams.**

![demo](https://raw.githubusercontent.com/Harsha2318/AI_AGENT_ARTICLE/main/static/demo.gif)

---

## 🚀 Features

- **AI-powered Article Generation**: Create in-depth articles on any topic using Google Gemini AI.
- **Dynamic Mermaid Diagrams**: Visualize concepts with auto-generated flow diagrams.
- **Customizable Content**: Adjust tone, complexity, target audience, and section structure.
- **Code & Reference Integration**: Embed code snippets and manage references easily.
- **SEO & Quality Analytics**: Get metrics on structure, readability, SEO, and more.
- **Modern UI**: Responsive, user-friendly, and visually appealing.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI
- **AI**: Google Gemini API
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Visualization**: Mermaid.js, Highlight.js
- **Database**: SQLite
- **Deployment**: Uvicorn

---

## 📦 Installation & Setup

```bash
# 1. Clone the repository
$ git clone https://github.com/Harsha2318/AI_AGENT_ARTICLE.git
$ cd AI_AGENT_ARTICLE

# 2. Create a virtual environment
$ python -m venv venv
# Activate (Windows)
$ .\venv\Scripts\activate
# Activate (Unix/Mac)
$ source venv/bin/activate

# 3. Install dependencies
$ pip install -r requirements.txt

# 4. Set up environment variables
$ echo GEMINI_API_KEY=your_api_key > .env
# (Get your key from https://makersuite.google.com/app/apikey)

# 5. Run the application
$ uvicorn app:app --reload
$ python app.py

# 6. Open in browser
# Visit: http://localhost:8000
```

---

## 🖥️ Demo

> **Try it out!**
>
> (https://drive.google.com/file/d/1vSox_vqn6XA2YMy2glsr4mphIl1bRdGs/view?usp=sharing)
>
> _Generate articles, visualize with Mermaid, and download markdown instantly._

---

## 📁 Project Structure

```text
AI_AGENT_ARTICLE/
├── app.py               # FastAPI backend
├── templates/
│   └── index.html       # Main HTML template
├── static/              # Static assets (CSS, JS, images)
├── requirements.txt     # Python dependencies
├── mermaid_integration.py # Mermaid diagram utilities
├── test.py              # URL scraping utility
├── .env                 # API keys & secrets
├── README.md            # This file
```

---

## 🌟 How It Works

1. **Enter a Topic**: Specify your topic and configure settings.
2. **Generate**: The app uses Gemini AI to create a structured article.
3. **Visualize**: Mermaid diagrams are generated and embedded.
4. **Download**: Export your article as markdown.

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b short-branch-name`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin <branch-name>`)
5. Open a Pull Request

---

## 🙏 Acknowledgments

- [Google Gemini AI](https://ai.google.com/) for language intelligence
- [FastAPI](https://fastapi.tiangolo.com/) for the backend framework
- [Mermaid.js](https://mermaid-js.github.io/) for diagram rendering
- [Bootstrap](https://getbootstrap.com/) for UI components
- [Highlight.js](https://highlightjs.org/) for code highlighting

---

## 📬 Author

- **Harsha P**  
  [GitHub](https://github.com/Harsha2318) • [Email](mailto:harshagowda2318@gmail.com)

---

## ⭐️ Show Your Support

If you found this project useful, please ⭐️ star the repo and share it!

---

<div align="center">
  <sub>Made with ❤️ by Harsha P | 2025</sub>
</div>

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



## 👤 Author

- **Harsha P**
- **Email**: harshagowda2318@gmail.com
- **GitHub**: [Harsha2318](https://github.com/Harsha2318)

## 🌟 Acknowledgments

- Google Gemini AI for the powerful language model
- FastAPI for the excellent web framework
- The open-source community for inspiration and tools
