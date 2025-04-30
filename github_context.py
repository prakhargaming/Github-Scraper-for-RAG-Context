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

def fetch_public_repo_information(username: str, generate_embeddings=False, directory="") -> dict[str, repo]:
    repo_url = f"https://api.github.com/users/{username}/repos"
    request_repo = requests.get(repo_url, headers=headers)
    if request_repo.status_code != 200:
        print(f"Request Failed (request_repo): {request_repo.status_code} \n {repo_url}")
        return request_repo.status_code
    data = request_repo.json()
    repo_info = []
    if directory != "":
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
            file_path = f"github_repos_info\\REPO_INFO_{repo_name}.txt"
            file_contents = generate_desc(repo_name, repo_url, repo_languages, repo_tags, repo_readme)
            try:
                with open(file_path, "w") as file:
                    file.write(file_contents)
                print(f"File '{file_path}' created successfully.")
            except Exception as e:
                print(f"An error occurred: {e}")

        repo_info.append(
            repo(
                name=repo_name,
                url=repo_url,
                languages=repo_languages,
                topics=auto_tag(repo_readme, repo_languages),
                readme=repo_readme,
                embedding=repo_embedding
            )
        )

    return repo_info

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", type=str, help="Enter your Github Username")
    parser.add_argument("embeddings", type=bool, help="Indicate whether you generate embeddings (requires Gemini API key in .env file)", default=False)
    parser.add_argument("mongo", type=bool, help="Indicate whether you want to push these documents to MongoDB (requires Mongo URI in .env file)", default=False)
    parser.add_argument("files", type=str, help="Indicate weather you want to save all the documents in a seperate folder", default="")
    parser.add_argument("database", type=str, help="If uploading to MongoDB, specify a database", default="")
    parser.add_argument("collection", type=str, help="If uploading to MongoDB, specify a collection", default="")
    args = parser.parse_args()
    
    load_dotenv()

    google_client = genai.Client(api_key=os.getenv("GEMINI"))

    if args.mongo and (args.database == "" or args.collection == ""):
        raise ValueError("You have opted to push your files to MongoDB. Please specify a collection and/or database to upload to.")

    GITHUB_TOKEN = os.getenv("REPO")

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    repos = fetch_public_repo_information(username=args.username, 
                                          generate_embeddings=args.embeddings, 
                                          generate_files=args.files)
    if args.mongo:    
        uri = os.getenv("MONGODB_URI")
        mongo_client = pymongo.MongoClient(uri, server_api=pymongo.server_api.ServerApi(
        version="1", strict=False, deprecation_errors=True))

        Prakharbase = mongo_client[args.database]
        vector_database = Prakharbase[args.collection]
        vector_database.insert_many(repos)