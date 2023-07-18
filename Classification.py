import os.path
from helpers.Text_extraction_utils import *
from fastapi import APIRouter, UploadFile, File, Body
import json
from helpers.JobDescription import jobDescription
from helpers.Transaction import *
out_file_path = os.path.abspath(os.path.curdir)

classification = APIRouter()

@classification.post("/extractData")
async def extract_data(files: List[UploadFile] = File(...), cluster: str = Body(...)):
    transaction = Transaction(cluster=cluster, type="Inserting Data", documents=[], date = int(time.time()))
    result = []
    for file in files:
        try:
            contents = file.file.read()

            working_path = os.path.join(Path.cwd(), "tmp_files", file.filename)
            with open(working_path, 'wb') as f:
                f.write(contents)
            f.close()
            page = pdf2image.convert_from_path(working_path)[0]
            page.save(working_path.replace(".pdf", ".jpg"), 'JPEG')
            thumb_link = upload_to_storage(working_path.replace(".pdf", ".jpg"), "thumbnails/Free")
            file_link = upload_to_storage(working_path, "Free")
            response = json.loads(process(working_path, cluster, thumb_link, file_link))
            transaction.cluster = response["cluster"]
            cv = response["id"]


        except Exception as e:
            return {"message": "There was an error uploading the file", "error": str(e)}

        result.append(cv)
    transaction.documents = result
    db.transactions.insert_one(transaction.dict())
    #removing the files
    for fil in os.walk(os.path.join(Path.cwd(), "tmp_files")):
        if os.path.isfile(fil) :
            os.remove(fil)
    return {"message": f"Successfully uploaded", "status": 200}


@classification.post("/extractDataFromFormat")
async def get_from_fillable(files: List[UploadFile] = File(...), cluster: str = Body(...)):
    transaction = Transaction(cluster=cluster, type="Inserting Forms", documents=[], date = int(time.time()))
    CVs = []
    for file in files:
        try:
            contents = file.file.read()
            working_path = os.path.join(Path.cwd(), "tmp_files", file.filename)
            with open(working_path, 'wb') as f:
                f.write(contents)
            pages = pdf2image.convert_from_path(working_path)[0]
            pages.save(working_path.replace(".pdf", ".jpg"), 'JPEG')
            thumb_link = upload_to_storage(working_path.replace(".pdf", ".jpg"), "thumbnails/Formatted")
            file_link = upload_to_storage(working_path, "Formatted")
            response = json.loads(get_text_from_fillable(working_path, cluster, thumb_link, file_link))
            CVs.append(response["id"])
        except Exception as e:
            return {"message": "There was an error uploading the file", "error": str(e)}
    transaction.documents = CVs
    db.transactions.insert_one(transaction.dict())
    # removing the files
    for fil in os.walk(os.path.join(Path.cwd(), "tmp_files")):
        if os.path.isfile(fil):
            os.remove(fil)
    return {"message": f"Successfully uploaded", "status": 200}


@classification.post("/getResumes")
async def get_resume(job: jobDescription, n: int = Body(...), cluster: str = Body(...)):
    transaction = Transaction(cluster=cluster, type="Profile Lookup", documents=[], date= int(time.time()))
    results = await get_top_profiles(job, cluster, n)
    transaction.documents = results["top_profiles"]
    transaction.cluster = results["cluster"]
    transaction.jobTitle = job.title
    db.transactions.insert_one(transaction.dict())
    return {"message": "Successfully uploaded", "status": 200, "results": json.dumps(results)}
