import copy
from docx2pdf import convert
import pdfplumber
from transformers import pipeline
from helpers.Resume import Resume, db
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import cv2
import pytesseract
import json
import os
import pdf2image
from pathlib import Path
from helpers.Utils import *
from fillpdf import fillpdfs
from helpers.FillableResume import FillableResume
from firebase_admin import storage, credentials, initialize_app
import time
from config import settings
from helpers.Clustering_utils import find_cluster_from_resume

cred = credentials.Certificate(settings.google_auth_path)
initialize_app(cred, {'storageBucket': settings.bucket_name})


def upload_to_storage(path, bucket_name):
    file_ref = storage.bucket(settings.bucket_name[:-1])
    blob = file_ref.blob(f"{bucket_name}/{int(time.time())}.pdf")
    blob.upload_from_filename(path)
    blob.make_public()
    return blob.public_url


def get_text_from_fillable(path, cluster, thumb_link, file_link):
    pdf = fillpdfs.get_form_fields(path)
    information = pdf.values()
    tags = ["firstName", "lastName", "email", "phoneArea", "phoneNumber", "education", "languages", "skills",
            "professional_experiences", "experience_Bool", "summary", "linkedin_link"]
    infos = list(information)[4:]
    result = {i: j for i, j in zip(tags, infos)}
    result["skills"] = result["skills"].replace("\xa0", "")
    result["professional_experiences"] = result["professional_experiences"].replace("\xa0", "")
    result["name"] = result["firstName"] + " " + result["lastName"]
    result["phone_number"] = result["phoneArea"] + result["phoneNumber"]
    result["cluster"] = cluster
    del result["firstName"]
    del result["lastName"]
    del result["phoneNumber"]
    del result["phoneArea"]
    del result['experience_Bool']
    result["professional_experiences"] = result["summary"]
    del result["summary"]
    result["file_link"] = file_link
    result["thumbnail_link"] = thumb_link

    resume = FillableResume(**result)
    ret = db.formatted_resumes.insert_one(resume.dict(by_alias=True)).inserted_id
    response = {"resume": result, "file_link": result["file_link"], "id": str(ret),
                "thumbnail_link": result["thumbnail_link"]}
    return json.dumps(response)


line_classifier = pipeline('text-classification', model='has-abi/distilBERT-finetuned-resumes-sections')
sections = ["skills", "professional_experiences", "contact/name/title", "certificates", "awards", "soft_skills",
            "professional_experiences", "interests", "projects", "summary", "languages", "education"]
separators = "\n;/,."


def predict(resume, job):
    text = [resume, job]
    cv = CountVectorizer()
    count_matrix = cv.fit_transform(text)
    matchpercentage = round(cosine_similarity(count_matrix)[0][1] * 100, 5)
    return matchpercentage


async def get_top_profiles(job, cluster, n):
    if cluster.lower() == "automatic":
        _cluster = find_cluster_from_resume(job)
    else:
        _cluster = cluster
    ret = db.JobDescriptions.insert_one(job.dict(by_alias=True)).inserted_id
    cursor = db["resumes"].find({'cluster': _cluster.lower()})
    cursor_formatted = db["formatted_resumes"].find({'cluster': _cluster.lower()})
    scores = {}
    experiences = ['other', 'entrylevel', 'junior', 'midlevel', 'senior', 'director']
    educations = ['other', 'highschool', 'associatedegree', 'bachelor', 'master', 'doctorate']
    for resume in cursor:
        prediction = predict(resume["skills"], " ".join(job.skills)) * 2
        prediction += (experiences.index(resume["professional_experiences"].replace(" ", "")) - experiences.index(job.experience)) * 1
        prediction += (educations.index(resume["education"].split("'")[0]) - educations.index(job.degree)) * 0.5
        prediction /= 3.5

        tmp_object = {"id": prediction, "thumb_link": resume["thumbnail_link"], "file_link": resume["file_link"],
                      "type": "free"}
        scores[str(resume["_id"])] = tmp_object

    for resume in cursor_formatted:
        prediction = predict(resume["skills"], " ".join(job.skills)) * 2
        prediction += (experiences.index(resume["professional_experiences"]) - experiences.index(job.experience)) * 1
        prediction += (educations.index(resume["education"]) - educations.index(job.education)) * 0.5
        prediction /= 3.5

        tmp_object = {"id": prediction, "thumb_link": resume["thumbnail_link"], "file_link": resume["file_link"],
                      "type": "formatted"}
        scores[str(resume["_id"])] = tmp_object

    scores = {k: v for k, v in sorted(scores.items(), reverse=True, key=lambda item: item[0])}
    selected = []
    for x in list(scores)[0:min(n, len(scores))]:
        tmp = scores[x]
        selected.append(tmp)

    return {"top_profiles": json.dumps(sorted(selected, key=lambda e: e["id"], reverse=True)), "cluster": _cluster}

def classify_sections(raw_data):
    results = {i: "" for i in sections}
    chunks = raw_data.split("SECTION_SEPARATORS")
    for chunk in chunks:
        try:
            counters = {i: 0 for i in sections}
            tmp = copy.deepcopy(chunk)
            for i in separators:
                tmp = "SEPARATORS".join(tmp.split(i))
            for i in tmp.split("SEPARATORS"):
                if i != "":
                    label = line_classifier(i)[0]['label']
                    counters[label] += 1
            if max(counters.values()) / sum(counters.values()) >= 0.8:
                results[max(counters, key=counters.get)] += chunk + " "
            else:
                label = line_classifier(chunk)[0]['label']
                if label in sections:
                    results[label] += chunk + " "
        except:
            pass
    return results


def get_text_by_section(path):
    if os.path.splitext(path)[1] == '.pdf':
        images = []
        image_from_pdf = pdf2image.convert_from_path(path)
        for i in range(len(image_from_pdf)):
            image_from_pdf[i].save(
                os.path.join(Path.cwd(), "tmp_files", "images", f'{os.path.splitext(path)[0].split("/")[-1]}_{i}.jpg'))
            image = cv2.imread(
                os.path.join(Path.cwd(), "tmp_files", "images", f'{os.path.splitext(path)[0].split("/")[-1]}_{i}.jpg'))
            images.append(image)
            os.remove(
                os.path.join(Path.cwd(), "tmp_files", "images", f'{os.path.splitext(path)[0].split("/")[-1]}_{i}.jpg'))
    elif(os.path.splitext(path)[1] == '.docx'):
        convert(path, path.replace(".docx", ".pdf"))
        images = []
        image_from_pdf = pdf2image.convert_from_path(path.replace(".docx", ".pdf"))
        for i in range(len(image_from_pdf)):
            image_from_pdf[i].save(
                os.path.join(Path.cwd(), "tmp_files", "images", f'{os.path.splitext(path)[0].split("/")[-1]}_{i}.jpg'))
            image = cv2.imread(
                os.path.join(Path.cwd(), "tmp_files", "images", f'{os.path.splitext(path)[0].split("/")[-1]}_{i}.jpg'))
            images.append(image)
            os.remove(
                os.path.join(Path.cwd(), "tmp_files", "images", f'{os.path.splitext(path)[0].split("/")[-1]}_{i}.jpg'))
    else:
        images = [cv2.imread(path)]
    result = ''
    for image in images:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 0)
        thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        dilate = cv2.dilate(thresh, kernel, iterations=4)

        cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = cnts[0] if len(cnts) == 2 else cnts[1]
        for c in cnts:
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 2)
            cropped = image[y:y + h, x:x + w]
            text = pytesseract.image_to_string(cropped)
            result += ("SECTION_SEPARATORS" + text_cleaning(text))
    return result


def process_v2(path, cluster="automatic", thumb_link="", file_link=""):
    try:
        raw_text = get_text_by_section(path)
        result = classify_sections(raw_text)
        result["others"] = result["contact/name/title"]
        result["cluster"] = cluster
        del result["contact/name/title"]
        for i in result.keys():
            if i != "professional_experiences":
                result[i] = text_cleaning(result[i])
        result["professional_experiences"] = xp_to_categories(extract_dates(result["professional_experiences"]))
        result["education"] = get_education(result["education"])
        result["file_link"] = file_link
        result["thumbnail_link"] = thumb_link
        resume = Resume(**result)
        if cluster.lower() == "automatic":
            _cluster = find_cluster_from_resume(resume)
            resume.cluster = _cluster
        ret = db.resumes.insert_one(resume.dict(by_alias=True)).inserted_id
        response = {"status": 200, "file_link": result["file_link"], "thumbnail_link": result["thumbnail_link"],
                    "id": str(ret), "cluster": resume.cluster}
        return json.dumps(response)
    except:
        response = {"status": 400, "message": "Error while processing the file"}
        return json.dumps(response)
