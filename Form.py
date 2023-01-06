from fastapi import File, UploadFile
from pydantic import BaseModel
from typing import List


class Form(BaseModel):
    title: str
    logo: str | None
    group: str
    desc: str | None
    files: List[UploadFile] | None
