from fastapi import APIRouter, File, UploadFile, Form
from app.pdf_parser import PDFParser
from app.vertex_ai import TextEmbedding
from app.config import config
from app import utils
import boto3
import os


gcp_secret = os.environ.get('GCP_SECRET')

ROUTE_NAME = "v1"

router = APIRouter(
    prefix=f"/{ROUTE_NAME}",
    tags=[ROUTE_NAME],
)


s3 = boto3.client('s3')


def upload_file_to_s3(file, file_key):
    s3.upload_fileobj(file.file, config.s3_bucket,
                      os.path.join(config.s3_root_dir, file_key))


embedding_model = TextEmbedding(
    secret=gcp_secret, batch_size=config.batch_size)
pdf_parser = PDFParser(embedding_model=embedding_model,
                       sentence_size=config.sentence_size,
                       overlapping_num=config.overlapping_num)


@router.post("/ingest_file")
async def ingest_file(file_key: str = Form(...), file: UploadFile = File(...)):
    upload_file_to_s3(file, file_key)

    return {'message': 'File uploaded successfully'}
