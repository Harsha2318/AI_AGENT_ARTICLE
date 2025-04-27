import subprocess
import tempfile
import os

def generate_mermaid_with_gemini(topic: str = None) -> str:
    # Delegate to the main implementation in app.py
    from app import generate_mermaid_with_gemini as impl
    return impl(topic=topic)

def mermaid_to_svg(mermaid_syntax: str) -> str:
    """
    Convert Mermaid syntax to SVG using the 'mmdc' CLI tool (Mermaid CLI).
    Requires Mermaid CLI installed globally (npm install -g @mermaid-js/mermaid-cli).
    Returns SVG content as string.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, "diagram.mmd")
        output_path = os.path.join(tmpdir, "diagram.svg")
        with open(input_path, "w") as f:
            f.write(mermaid_syntax)
        try:
            # Add '-q' to suppress Mermaid CLI log output
            subprocess.run([r"C:\\Users\\harsh\\AppData\\Roaming\\npm\\mmdc.cmd", "-i", input_path, "-o", output_path, "-q"], check=True)
            with open(output_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
            return svg_content
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Mermaid CLI conversion failed: {e}")

if __name__ == "__main__":
    # Example usage
    topic = "AI Article Generator"
    mermaid_code = generate_mermaid_with_gemini(topic)
    print("Mermaid Syntax:")
    print(mermaid_code)
    try:
        svg = mermaid_to_svg(mermaid_code)
        print("Generated SVG:")
        print(svg)
    except Exception as e:
        print(f"Error rendering Gemini diagram, using fallback template. Reason: {e}")
        fallback_code = f"""
        flowchart TD
            A[Start] --> B[{topic} Research]
            B --> C[Data Processing]
            C --> D[Model Training]
            D --> E[Deployment]
            E --> F[User Interaction]
        """
        try:
            svg = mermaid_to_svg(fallback_code.strip())
            print("Fallback SVG:")
            print(svg)
        except Exception as e2:
            print(f"Fallback also failed: {e2}")
