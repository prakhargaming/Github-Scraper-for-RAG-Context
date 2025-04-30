def auto_tag(readme_text, languages) -> list[str]:
    tags = []

    # Keywords for different skill areas
    computer_vision_keywords = ["opencv", "cnn", "image", "vision", "detection", "segmentation", "recognition"]
    nlp_keywords = ["bert", "transformer", "token", "nlp", "text classification", "language model"]
    web_dev_keywords = ["react", "flask", "django", "express", "api", "frontend", "backend", "web app"]
    data_science_keywords = ["pandas", "numpy", "dataframe", "analysis", "plot", "visualization"]
    ai_keywords = ["deep learning", "machine learning", "reinforcement learning", "model", "training"]

    text = readme_text.lower()

    # Helper function
    def contains_any(keywords):
        return any(keyword in text for keyword in keywords)

    # Tagging based on content
    if contains_any(computer_vision_keywords) or 'OpenCV' in languages:
        tags.append("computer-vision")
    if contains_any(nlp_keywords):
        tags.append("nlp")
    if contains_any(web_dev_keywords):
        tags.append("web-development")
    if contains_any(data_science_keywords):
        tags.append("data-science")
    if contains_any(ai_keywords):
        tags.append("artificial-intelligence")

    return tags

def generate_desc(name="", url="", languages="", tags="", readme=""):
    return f"""
# METADATA
Repository name: {name}
Repository URL: {url}
Repository languages: {languages}
Repository topics: {tags}

# README:
{readme}"""