from typing import List
import vertexai
from vertexai.language_models import TextEmbeddingModel
import google.auth
from app.utils import decode_secret_dict
from tqdm import tqdm


class TextEmbedding():
    def __init__(self, secret, batch_size=64):
        secret_dict = decode_secret_dict(secret)
        self.batch_size = batch_size
        self.credentials, self.project = google.auth.load_credentials_from_dict(
            info=secret_dict, scopes=[
                "https://www.googleapis.com/auth/cloud-platform"]
        )

        vertexai.init(project=self.project, credentials=self.credentials)

        self.model = TextEmbeddingModel.from_pretrained(
            "textembedding-gecko@003")

    def get_embeddings(self, sentences: List[str]) -> List:
        embeddings = self.model.get_embeddings(
            sentences, auto_truncate=True)
        return [embedding.values for embedding in embeddings]

    def __call__(self, sentences: List[str], batch_size=64) -> List[List[float]]:

        if batch_size:
            self.batch_size = batch_size

        embeddings = []

        for i in tqdm(range(0, len(sentences), batch_size)):
            batch = sentences[i:i+batch_size]
            embeddings.extend(self.get_embeddings(batch))

        return embeddings
