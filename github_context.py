import requests
import pymongo
import os
import base64
import argparse

from typing import TypedDict
from google import genai
from utils import generate_desc, auto_tag
from google.genai import types
from dotenv import load_dotenv

class repo(TypedDict):
    name: str
    url: str
    languages: dict[str, int]
    topics: list[str]
    readme: str
    embedding: list[float]

def fetch_public_repo_information(username: str, generate_embeddings=False, directory="") -> list[repo]:
    if args.embeddings:
        google_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    headers = {
        "Authorization": f"token {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    repo_url = f"https://api.github.com/users/{username}/repos"
    request_repo = requests.get(repo_url, headers=headers)
    if request_repo.status_code != 200:
        print(f"Request Failed (request_repo): {request_repo.status_code} \n {repo_url}")
        return request_repo.status_code
    data = request_repo.json()
    repo_info = []
    if directory:
        os.makedirs(directory, exist_ok=True)
    for repos in data:
        repo_name = repos["name"]
        repo_url = repos["url"]
        language_url = f"https://api.github.com/repos/{username}/{repo_name}/languages"
        readme_url = f"https://api.github.com/repos/{username}/{repo_name}/readme"

        request_languages = requests.get(language_url, headers=headers)
        if request_languages.status_code == 200:     
            repo_languages = request_languages.json()
        else:
            print(f"Request Failed (request_languages): {request_languages.status_code} \n {language_url}")
            repo_languages = {}

        request_readme = requests.get(readme_url, headers=headers)
        if request_readme.status_code == 200:
            readme_content = request_readme.json()
            repo_readme = base64.b64decode(readme_content["content"]).decode('utf-8')
        else:
            print(f"Request Failed (request_readme): {request_readme.status_code} \n {readme_url}")
            repo_readme = ""
        
        repo_tags = auto_tag(repo_readme, repo_languages)
        
        if generate_embeddings:
            to_embed = generate_desc(repo_name, repo_url, repo_languages, repo_tags, repo_readme)
            result = google_client.models.embed_content(
                model="text-embedding-004",
                contents=to_embed,
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
            )
            repo_embedding = result.embeddings[0].values
        else:
            repo_embedding = []

        if directory != "":
            file_path = os.path.join(directory, f"REPO_INFO_{repo_name}.txt")
            file_contents = generate_desc(repo_name, repo_url, repo_languages, repo_tags, repo_readme)
            try:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(file_contents)
                print(f"File '{file_path}' created successfully.")
            except Exception as e:
                print(f"An error occurred: {e}")

        repo_info.append(
            repo(
                name=repo_name,
                url=repo_url,
                languages=repo_languages,
                topics=repo_tags,
                readme=repo_readme,
                embedding=repo_embedding
            )
        )

    return repo_info


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("username", type=str, help="Enter your GitHub Username")
    parser.add_argument("--embeddings", action="store_true", help="Generate embeddings (requires GEMINI API key)")
    parser.add_argument("--mongo", action="store_true", help="Push to MongoDB (requires MONGO URI)")
    parser.add_argument("--save-files", action="store_true", help="Save documents to local folder")
    parser.add_argument("--files-dir", type=str, default="./output", help="Directory to save files")
    parser.add_argument("--database", type=str, help="MongoDB database name (required if --mongo is set)")
    parser.add_argument("--collection", type=str, help="MongoDB collection name (required if --mongo is set)")

    args = parser.parse_args()
    load_dotenv()

    if args.mongo and (not args.database or not args.collection):
        raise ValueError("You used --mongo but did not specify --database and/or --collection.")

    repos = fetch_public_repo_information(
        username=args.username,
        generate_embeddings=args.embeddings,
        directory=args.files_dir if args.save_files else ""
    )

    if args.mongo:
        uri = os.getenv("MONGODB_URI")
        mongo_client = pymongo.MongoClient(uri, server_api=pymongo.server_api.ServerApi(
            version="1", strict=False, deprecation_errors=True
        ))
        database = mongo_client[args.database]
        collection = database[args.collection]
        collection.insert_many(repos)
