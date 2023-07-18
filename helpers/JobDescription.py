from pydantic import BaseModel
from bson import ObjectId
from pymongo import MongoClient
import sys
from pathlib import Path
from typing import List


external_path = Path.cwd()
sys.path.insert(1, str(external_path))

from config import settings

client = MongoClient(f"mongodb+srv://{settings.MongoDB_username}:{settings.MongoDB_password}@{settings.MongoDB_id}/?retryWrites=true&w=majority")
db = client.test


class PyObjectId(ObjectId):

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type='string')


class jobDescription(BaseModel):
    title: str
    description: str
    experience: str
    degree: str
    date: str
    skills: List[str]

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str
        }
