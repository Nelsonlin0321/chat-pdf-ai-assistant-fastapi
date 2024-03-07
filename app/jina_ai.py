from typing import List
import requests


class JinaAI():
    def __init__(self, api_key) -> None:

        self.api_key = api_key
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

    def get_embeddings(self, chunks) -> List[List[float]]:

        url = 'https://api.jina.ai/v1/embeddings'
        data = {
            'input': chunks,
            'model': 'jina-embeddings-v2-base-en'
        }

        response = requests.post(url, headers=self.headers, json=data)

        return [item['embedding'] for item in response.json()['data']]

    def rerank(self, query, chunks, top_n=5) -> List[int]:

        url = "https://api.jina.ai/v1/rerank"

        data = {
            "model": "jina-reranker-v1-base-en",
            "query": query,
            "documents": chunks,
            "top_n": top_n
        }

        response = requests.post(url, headers=self.headers, json=data)

        reranked_indices = [item["index"]
                            for item in response.json()['results']]

        return reranked_indices
