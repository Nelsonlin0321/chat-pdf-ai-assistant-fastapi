from fastapi import APIRouter, File, UploadFile, Form
from app.pdf_parser import PDFParser
from app.vertex_ai import TextEmbedding
from app.config import config
from app import utils
import boto3
import os
from app.mongodb_engine import MongoDB
import pandas as pd

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
def keyword_search(query: str, file_key: str, limit: int = 5):
    results = mongo_db_engine.keyword_search(
        query=query, file_key=file_key, limit=limit)
    return results


@router.post("/hybrid_search")
def hybrid_search(query: str, file_key: str, limit: int = 5):
    keyword_search_results = keyword_search(
        query=query, file_key=file_key, limit=limit)
    vector_search_results = vector_search(
        query=query, file_key=file_key, limit=limit)
    results = combine_vector_keyword_search(vector_search_results=vector_search_results,
                                            keyword_search_results=keyword_search_results, limit=limit)
    return results


def normalized_score(df):
    max_score = max(df['score'])
    min_score = min(df['score'])
    if (max_score-min_score) == 0:
        df['normalized_score'] = 1
    else:
        df['normalized_score'] = df['score'].apply(
            lambda x: (x-min_score)/(max_score-min_score))
    return df


def combine_vector_keyword_search(vector_search_results, keyword_search_results, limit: int = 5):

    chunk_id = "chunk_id"

    if len(vector_search_results) == 0 and len(keyword_search_results) == 0:
        return []

    if len(vector_search_results) == 0:
        return vector_search_results

    if len(keyword_search_results) == 0:
        return keyword_search_results

    df_keyword_search = pd.DataFrame(keyword_search_results)
    df_vector_search = pd.DataFrame(vector_search_results)

    both_hit_indices = set(df_vector_search[[chunk_id]].merge(
        df_keyword_search[[chunk_id]])[chunk_id])

    rest_size = limit - len(both_hit_indices)

    df_vector_search = normalized_score(df_vector_search)
    df_vector_search['search_type'] = "vector_search"
    df_keyword_search = normalized_score(df_keyword_search)
    df_keyword_search['search_type'] = "keyword_search"

    df_hybrid_search = pd.concat(
        [df_keyword_search, df_vector_search])

    df_hybrid_search_1 = df_keyword_search[df_keyword_search[chunk_id].isin(
        both_hit_indices)].copy()

    df_hybrid_search_1['both_hit'] = True

    df_hybrid_search_2 = df_hybrid_search[~df_hybrid_search[chunk_id].isin(
        both_hit_indices)].copy()

    df_hybrid_search_2 = df_hybrid_search_2.sort_values(
        by='normalized_score', ascending=False).head(rest_size)

    df_hybrid_search_2['both_hit'] = False

    df_hybrid_search = pd.concat([df_hybrid_search_1, df_hybrid_search_2])

    results = df_hybrid_search.to_dict(orient='records')

    return results
