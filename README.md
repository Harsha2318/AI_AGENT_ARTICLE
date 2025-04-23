# AI Article Generator

AI Article Generator is a Python-based tool that leverages advanced AI models like Google's Gemini and SerpApi to generate SEO-optimized, comprehensive articles. It supports brand voice training, competitor research, and content generation with expert quotes, key facts, and FAQ sections to create engaging and factually accurate articles.

## Features

- Train the AI on your brand voice using URLs or text samples
- Research topics with SERP analysis and competitor content insights
- Generate SEO-optimized articles with structured outlines and keyword integration
- Include expert quotes, key facts, and FAQ sections automatically
- Save generated articles as markdown files for easy publishing

## Installation

1. Clone the repository:

   ```bash
   git clone <repository-url>
   cd AI_ARTICLEGENERATOR
   ```

2. Create and activate a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up your API keys:

   - Create a `.env` file in the project root directory.
   - Add your Gemini API key and SerpApi key:

     ```
     GEMINI_API_KEY=your_gemini_api_key_here
     SERPAPI_KEY=your_serpapi_key_here
     ```

## Usage

Run the main script to generate an article:

```bash
python generate_article.py
```

The script will:

1. Train the AI on your brand voice using predefined URLs (you can modify these in the script).
2. Prompt you to enter the article topic, primary keyword, and secondary keywords.
3. Research the topic using SERP analysis and competitor content.
4. Generate a comprehensive, SEO-optimized article.
5. Save the article as a markdown file named after the topic.

## Output

The generated article will be saved as a `.md` file in the project directory, ready for publishing or further editing.

## Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the project.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
