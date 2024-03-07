from pydantic import BaseModel


class DeleteFilePayLoad(BaseModel):
    file_key: str
