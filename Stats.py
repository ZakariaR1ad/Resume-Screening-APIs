import json

import pymongo

from helpers.Utils import get_month_from_sec
from fastapi import APIRouter
from pymongo import MongoClient
from config import settings

stats = APIRouter()


try:
    client = MongoClient(f"mongodb+srv://{settings.MongoDB_username}:{settings.MongoDB_password}@{settings.MongoDB_id}/?retryWrites=true&w=majority")
    db = client.test
except:
    print("Connection to database failed")


@stats.get("/Profiles")
async def get_count():
    return {"FreeResumeCount": db.resumes.count_documents({}), "FormattedResumeCount": db.formatted_resumes.count_documents({})}


@stats.get("/MonthlyProfiles")
async def get_count_per_month():
    return {"FreeResumeCount": db.resumes.count_documents({}), "FormattedResumeCount": db.formatted_resumes.count_documents({})}


@stats.get("/Transactions")
async def get_transactions(n):
    transactions = db.transactions.find().sort("date", -1).limit(int(n))
    transactions = list(transactions)
    for transaction in transactions:
        transaction["_id"] = str(transaction["_id"])
    return {"transactions": json.dumps(list(transactions))}


@stats.get("/v1/getStats")
async def get_stats():
    try:
        transactions = db.transactions.find({}).sort("date", pymongo.DESCENDING).limit(100)
        lookup_year = [0]*12
        insertion_year = [0]*12
        list_of_transactions = []
        for transaction in transactions:
            transaction["_id"] = str(transaction["_id"])
            list_of_transactions.append(transaction)
            if transaction["type"] == "Profile Lookup":
                lookup_year[get_month_from_sec(transaction["date"])] += 1
            else:
                insertion_year[get_month_from_sec(transaction["date"])] += 1

        for l in list_of_transactions:
            l["_id"] = str(l["_id"])
        transactionscnt = len(list_of_transactions)
        freecnt = db.resumes.count_documents({})
        fillablecnt = db.formatted_resumes.count_documents({})
        stats = {
            "Cvscnt": freecnt+fillablecnt,
            "transactionscnt": transactionscnt,
            "lookup_year": lookup_year,
            "insertion_year": insertion_year,
            "freecnt": freecnt,
            "fillablecnt": fillablecnt,
            "transactions": json.dumps(list_of_transactions),
        }
    except Exception as e:
        print(str(e))
        return {"message": "Internal error", "status": 500}
    return json.dumps(stats)
