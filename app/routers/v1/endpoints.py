from fastapi import APIRouter, File, UploadFile
from app import utils
import boto3
import os

ROUTE_NAME = "v1"

router = APIRouter(
    prefix=f"/{ROUTE_NAME}",
    tags=[ROUTE_NAME],
)


s3 = boto3.client('s3')


def upload_file_to_s3(file_path, object_name):
    s3.upload_file(file_path, "cloudfront-aws-bucket",
                   os.path.join("chinese-local-rag", object_name))


@router.post("/ingest_file")
async def ingest_file(file: UploadFile = File(...)):
    save_file_path = utils.save_file(file=file)

    upload_file_to_s3(save_file_path, os.path.basename(save_file_path))

    message = chroma_engine.ingest_file(
        file_path=save_file_path,
        sentence_size=256,
        overlapping_num=2,
        overwrite=True)

    return message
