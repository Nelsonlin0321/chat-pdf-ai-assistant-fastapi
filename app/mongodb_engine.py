from typing import Dict, List
from pymongo import MongoClient

DB_NAME = "RAG"
FILE_COLLECTION = "UploadedFile"
EMBEDDING_COLLECTION = "Embedding"


class MongoDB():

    def __init__(self, mongodb_url) -> None:
        self.client = MongoClient(mongodb_url)
        self.db_name = DB_NAME
        self.db = self.client[self.db_name]

    def file_exist(self, file_name: str) -> bool:
        collection = self.db[FILE_COLLECTION]
        results = collection.find_one({"file_name": file_name})
        return results is not None

    def insert_file(self, file_name: str, file_key, full_text: str) -> None:
        # if not self.file_exist(file_name):
        collection = self.db[FILE_COLLECTION]

        if file_key.startswith('/'):
            file_key = file_key[1:]

        result = collection.insert_one(
            {'file_name': file_name,
             'file_key': file_key,
             "file_url": f"https://d2gewc5xha837s.cloudfront.net/{file_key}",
             'full_text': full_text}
        )
        return result

    def insert_embedding(self, embeddings) -> List:
        # if not self.file_exist(file_name):
        collection = self.db[EMBEDDING_COLLECTION]
        collection.insert_many(embeddings)

    def vector_search(self, query_vector: List[float],
                      file_key: str, limit: int = 5) -> List[Dict]:

        # create a vector search index
        # {
        #   "fields": [
        #     {
        #       "numDimensions": 768,
        #       "path": "embedding",
        #       "similarity": "dotProduct",
        #       "type": "vector"
        #     },
        #     {
        #       "path": "file_key",
        #       "type": "filter"
        #     },
        #     {
        #       "path": "chat_id",
        #       "type": "filter"
        #     }
        #   ]
        # }

        results = self.db[EMBEDDING_COLLECTION].aggregate([
            {

                "$vectorSearch": {
                    "index": "vector_index",
                    "path": "embedding",
                    "queryVector": query_vector,
                    "numCandidates": limit,
                    "limit": limit,
                    "filter": {"file_key": {"$eq": file_key}}
                }

            },
            {

                '$project': {
                    'embedding': 0,
                    "_id": 0,
                    'uploaded_file_id': 0,
                    "chat_id": 0,
                    "file_key": 0,
                    "score": {"$meta": "vectorSearchScore"},
                }

            }

        ])

        return list(results)

    def keyword_search(self, query: str, file_key: str, limit: int = 5) -> List[Dict]:

        search_query = [
            {
                '$search': {
                    'index': 'default',
                    'compound': {
                        'filter': [
                            {
                                'text': {
                                    'query': file_key,
                                    'path': 'file_key'
                                }
                            }
                        ],
                        'must': [
                            {
                                'text': {
                                    'query': query,
                                    'path': 'text'
                                }
                            }
                        ]
                    }
                }
            }, {
                '$addFields': {
                    'score': {
                        '$meta': 'searchScore'
                    }
                }
            }, {
                '$project': {
                    'embedding': 0,
                    "_id": 0,
                    'uploaded_file_id': 0,
                    "chat_id": 0,
                    "file_key": 0,
                }
            }, {
                '$limit': limit
            }
        ]

        results = list(self.db[EMBEDDING_COLLECTION].aggregate(search_query))

        return results
