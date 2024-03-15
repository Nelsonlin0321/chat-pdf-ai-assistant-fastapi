import os
import numpy as np
import boto3
from app import utils
from app.config import config
from app.jina_ai import JinaAI
from app.mongodb_engine import MongoDB
from app.pdf_parser import PDFParser
from fastapi import APIRouter, File, UploadFile, Form
import dotenv
import datetime

from app.routers.v1.payload import DeleteFilePayLoad
dotenv.load_dotenv()


ROUTE_NAME = "v1"

router = APIRouter(
    prefix=f"/{ROUTE_NAME}",
    tags=[ROUTE_NAME],
)


s3 = boto3.client('s3')


def upload_file_to_s3(file_path, file_key):
    s3.upload_file(file_path, config.s3_bucket, file_key)


pdf_parser = PDFParser(sentence_size=config.sentence_size,
                       overlapping_num=config.overlapping_num)

mongo_db_engine = MongoDB(mongodb_url=os.getenv("MONGODB_URL"))
jina_ai = JinaAI(api_key=os.getenv("JINA_API_KEY"))


@router.post("/ingest_file")
async def ingest_file(file_key: str = Form(...), chat_id: str = Form(...), file: UploadFile = File(...)):

    file_path = utils.save_file(file=file)
    upload_file_to_s3(file_path, file_key)

    full_text, chunk_metas = pdf_parser.parse(file_path=file_path)

    chunks = [chunk['text'] for chunk in chunk_metas]
    embeddings = jina_ai.get_embeddings(chunks)
    for embedding, metas in zip(embeddings, chunk_metas):
        metas['embedding'] = embedding

    file_name = os.path.basename(file_key)
    _ = mongo_db_engine.insert_file(
        file_name, file_key, full_text)

    for chunk in chunk_metas:
        chunk['chat_id'] = chat_id
        chunk['file_key'] = file_key
        chunk['file_name'] = file_name

    # chunk_metas: List[
    # {"text": str,
    # "page_number": List[int]),
    # "word_size": int,
    # "chunk_id": int
    # "file_name": str,
    # "embedding": List[List[float]]
    # "file_key":str
    # uploaded_file_id: str
    # chat_id: str
    # }[

    mongo_db_engine.insert_embedding(chunk_metas)

    return {"messages": "Ingested file successfully"}


@router.get("/vector_search")
async def vector_search(query: str, chat_id: str, limit: int = 5):

    embedding = jina_ai.get_embeddings([query])[0]

    results = mongo_db_engine.vector_search(
        query_vector=embedding, chat_id=chat_id, limit=limit)

    return results


@router.get("/keyword_search")
async def keyword_search(query: str, chat_id: str, limit: int = 5):
    results = mongo_db_engine.keyword_search(
        query=query, chat_id=chat_id, limit=limit)

    return results


@router.get("/hybrid_search")
async def hybrid_search(query: str, chat_id: str, limit: int = 5):
    keyword_search_results = await keyword_search(
        query=query, chat_id=chat_id, limit=limit)

    vector_search_results = await vector_search(
        query=query, chat_id=chat_id, limit=limit)

    deduplicated_search_result = deduplicate(vector_search_results,
                                             keyword_search_results, id_field='chunk_id')

    chunks = [item["text"] for item in deduplicated_search_result]

    reranked_indics, relevance_scores = jina_ai.rerank(
        query=query, chunks=chunks, top_n=limit)

    reranked_results = np.array(deduplicated_search_result)[
        reranked_indics].tolist()

    for score, item in zip(relevance_scores, reranked_results):
        item["score"] = score

    return reranked_results


@router.delete("/delete_file")
async def delete_file(payload: DeleteFilePayLoad):
    file_key = payload.file_key

    s3.delete_object(
        Bucket=config.s3_bucket,
        Key=file_key
    )

    return {"message": "File deleted successfully"}


def deduplicate(search_results_1, search_results_2, id_field):

    deduplicated = search_results_1.copy()

    search_ids = set([item[id_field]
                      for item in search_results_1])

    for item in search_results_2:
        if item[id_field] not in search_ids:
            deduplicated.append(item)

    return deduplicated


DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
start_time = now_hk = datetime.datetime.now(
    datetime.timezone(datetime.timedelta(hours=8)))
start_time = start_time.strftime(DATE_FORMAT)


@router.get(f"/health_check")
async def health_check():
    response = f"The server is up since {start_time}"
    return {"message": response, "start_hk_time": start_time}