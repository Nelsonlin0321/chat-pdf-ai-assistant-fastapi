from typing import Optional
from pydantic import BaseModel


class UploadFilePayLoad(BaseModel):
    file_key: str = "1/investment_policy_guidelines.pdf"
