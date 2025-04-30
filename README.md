# Github Context Scraper for RAG Context

This script will scape a user's public Github repos for important information to be used for a RAG-enabled LLM. This script was written to create a a vector search index database for [prakhargaming.com](https://prakhargaming.com).

## Prequisites
You need to create a `.env` File: Once you clone the repo, you need to create a .env file with these API keys for the following features:
   1. **Github Personal Access Token** The token is only used to send authenticated requests to Github's API. You can also use another type of authentication token as well.
   2. **Gemini API Key** This key is used to access the Google Embedding models to generate embeddings.
   3. **MongoDB Atlas URI** The URI will be used to create vector search index database in your MongoDB database.

## How it Works
1. First, a request is made to pull all the repositories available under a certain user. 
2. After we have a list of all the repos, a `TypedDict` object is instantiated on a per-repo basis:
   ```py
   class repo(TypedDict):
       name: str
       url: str
       languages: dict[str, int]
       topics: list[str]
       readme: str
       embedding: list[float]
3. Additionally, if the user opts to create embeddings, a request is sent to Google's Gemini API to generate an embedding with their `"text-embedding-004"` model.
4. Finally, all documents are pushed to MongoDB according to the schema outlined earlier.

## How to Use
```bash
python3 github_context.py your-github-username --embeddings --mongo --database myDB --collection myCollection --save-files --files-dir ./output