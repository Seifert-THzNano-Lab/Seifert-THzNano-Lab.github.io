import os
import re
import requests
from serpapi import GoogleSearch
from util import *

def find_doi_by_title(title):
    """Queries Crossref API to find a DOI for a given title"""
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={requests.utils.quote(title)}&rows=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        items = data.get('message', {}).get('items', [])
        if items:
            # Check if the title is a close enough match (optional but recommended)
            return items[0].get('DOI')
    except:
        pass
    return None

def main(entry):
    api_key = os.environ.get("GOOGLE_SCHOLAR_API_KEY", "")
    if not api_key:
        raise Exception('No "GOOGLE_SCHOLAR_API_KEY" env var')

    params = {
        "engine": "google_scholar_author",
        "api_key": api_key,
        "num": 100,
    }

    _id = get_safe(entry, "gsid", "")
    if not _id:
        raise Exception('No "gsid" key')

    @log_cache
    @cache.memoize(name=__file__, expire=1 * (60 * 60 * 24))
    def query(_id):
        params["author_id"] = _id
        return get_safe(GoogleSearch(params).get_dict(), "articles", [])

    response = query(_id)
    sources = []

    for work in response:
        title = get_safe(work, "title", "")
        link = get_safe(work, "link", "")
        year = get_safe(work, "year", "")
        
        cite_id = ""
        
        # 1. Try to find DOI in the link provided by SerpApi
        doi_match = re.search(r'doi\.org\/(10\.\d{4,}\/[-._;()/:a-zA-Z0-9]+)', link)
        if doi_match:
            cite_id = f"doi:{doi_match.group(1)}"
        
        # 2. NEW: Use Crossref API to find the DOI by Title
        if not cite_id and title:
            found_doi = find_doi_by_title(title)
            if found_doi:
                cite_id = f"doi:{found_doi}"
        
        # 3. Last resort: If still no DOI, use a URL (Manubot can often parse those)
        if not cite_id:
            cite_id = link if link else get_safe(work, "citation_id", "")

        source = {
            "id": cite_id,
            "title": title,
            "authors": list(map(str.strip, get_safe(work, "authors", "").split(","))),
            "publisher": get_safe(work, "publication", ""),
            "date": (year + "-01-01") if year else "",
            "link": link,
        }
        source.update(entry)
        sources.append(source)

    return sources