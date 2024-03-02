import os
from typing import List
import vertexai
from vertexai.language_models import TextEmbeddingModel
import google.auth
from app.utils import decode_secret_dict
from tqdm import tqdm
import dotenv
dotenv.load_dotenv()


GCP_SECRET = os.getenv("GCP_SECRET")
if not GCP_SECRET:
    # pylint: disable=broad-exception-raised
    raise Exception("GCP_SECRET is not defined")


class TextEmbedding():
    def __init__(self, secret=None, batch_size=64):

        if secret:
            secret_dict = decode_secret_dict(secret)
        else:
            secret_dict = decode_secret_dict(GCP_SECRET)

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
            texts=sentences, auto_truncate=True)
        return [embedding.values for embedding in embeddings]

    def __call__(self, sentences: List[str], batch_size=64) -> List[List[float]]:

        if batch_size:
            self.batch_size = batch_size

        embeddings = []

        for i in tqdm(range(0, len(sentences), batch_size)):
            batch = sentences[i:i+batch_size]
            embeddings.extend(self.get_embeddings(batch))

        return embeddings
