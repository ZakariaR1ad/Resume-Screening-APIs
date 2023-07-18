import re
import time
from langdetect import detect

def extract_dates(s):
    years = re.findall(r"([0-9]{4})", s)
    return years


def years_to_xp(years):
    sorted_years = [int(i) for i in list(sorted(years))]
    xp = max(sorted_years)-min(sorted_years)
    for y in range(1, len(sorted_years)-1, 2):
        xp = xp - (sorted_years[y+1]-sorted_years[y])
    return xp


def xp_to_categories(years):
    xp = years_to_xp([int(y) for y in years])
    if xp >= 15: return "director"
    elif xp >= 8: return "senior"
    elif xp >= 2: return "midlevel"
    elif xp >= 1: return "junior"
    else: return "entry level"


def text_cleaning(text):
    text_cleaning_re = "@\S+|https?:\S+|http?:\S+|[^A-Za-z0-9]:\S+|nbsp"
    special = r'[^a-zA-z0-9.,!?/:;\"\'\s]'
    text = re.sub(text_cleaning_re, ' ', str(text).lower()).strip()
    text = re.sub(special, '', str(text).lower()).strip()
    return text


def get_month_from_sec(secs):
    secs = int(secs)
    secs = time.gmtime(secs)
    secs = secs.tm_mon-1
    return secs


def get_education(raw):
    try:
        lang = detect(raw)
        if lang != "en" and lang != "fr":
            return "other"
        elif lang == "en":
            ranking = ["bachelor", "master", "doctorate", "phd", "postdoctoral"]
            pattern = r"\b(bachelor(?:'s)?|master(?:'s)?|doctor(?:ate|al)?|ph\.?d|postdoc(?:toral)?)\b"
            matches = re.findall(pattern, raw, re.IGNORECASE)
            scores = [ranking.index(m.split("'")[0].lower()) for m in matches]
            if matches:
                highest_education = matches[scores.index(max(scores))]
                # Select the longest match
                return highest_education
            return "other"
        else:
            ranking = ["licence", "master", "doctorat", "postdoctoral"]
            pattern = r"\b(licence?|master?|doctor(?:at|al)?|ph\.?d|postdoc(?:toral)?)\b"
            matches = re.findall(pattern, raw, re.IGNORECASE)

            if matches:
                highest_education = max(matches, key=ranking.index)  # Select the longest match
                return highest_education
            return "other"

    except:
        return "other"


