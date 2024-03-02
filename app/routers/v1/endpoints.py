from fastapi import APIRouter, File, UploadFile, Form
from app.pdf_parser import PDFParser
from app.vertex_ai import TextEmbedding
from app.config import config
from app import utils
import boto3
import os
from app.mongodb_engine import MongoDB

gcp_secret = os.environ.get('GCP_SECRET')

ROUTE_NAME = "v1"

router = APIRouter(
    prefix=f"/{ROUTE_NAME}",
    tags=[ROUTE_NAME],
)


s3 = boto3.client('s3')


def upload_file_to_s3(file_path, file_key):
    s3.upload_file(file_path, config.s3_bucket, file_key)


embedding_model = TextEmbedding(
    secret=gcp_secret, batch_size=config.batch_size)
pdf_parser = PDFParser(embedding_model=embedding_model,
                       sentence_size=config.sentence_size,
                       overlapping_num=config.overlapping_num)

mongo_db_engine = MongoDB()


@router.post("/ingest_file")
async def ingest_file(file_key: str = Form(...), chat_id: str = Form(...), file: UploadFile = File(...)):

    file_path = utils.save_file(file=file)
    upload_file_to_s3(file_path, file_key)

    full_text, chunks_with_embeddings = pdf_parser.parse(file_path=file_path)

    # chunks_with_embeddings: List[
    # {"text": str,
    # "page_number": List[int]),
    # "word_size": int,
    # "chunk_id": int
    # }[

    file_name = os.path.basename(file_key)
    inserted_file = mongo_db_engine.insert_file(
        file_name, file_key, full_text)

    uploaded_file_id = inserted_file.inserted_id

    for chunk in chunks_with_embeddings:
        chunk['chat_id'] = chat_id
        chunk['uploaded_file_id'] = uploaded_file_id
        chunk['file_key'] = file_key

    mongo_db_engine.insert_embedding(chunks_with_embeddings)

    return {"messages": "Ingested file successfully"}


@router.post("/vector_search")
def vector_search(query: str, file_key: str, limit: int = 5):
    embedding = embedding_model([query])[0]

    results = mongo_db_engine.vector_search(
        query_vector=embedding, file_key=file_key, limit=limit)

    return results


@router.post("/keyword_search")
def vector_search(query: str, file_key: str, limit: int = 5):
    results = mongo_db_engine.keyword_search(
        query=query, file_key=file_key, limit=limit)
    return results
