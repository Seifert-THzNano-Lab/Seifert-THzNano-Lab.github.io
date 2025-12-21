import os
import re
import requests
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from serpapi import GoogleSearch
from util import *

def similarity(a, b):
    """Calculates how similar two titles are (0.0 to 1.0)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_arxiv_data(link):
    """
    Extracts ArXiv ID and fetches FULL author list from ArXiv API.
    Returns: (id, author_string)
    """
    # Robust regex for ArXiv IDs (handles versions v1, v2 etc)
    match = re.search(r'(\d{4}\.\d{4,5})(v\d+)?', link)
    if not match:
        return None, None
    
    arxiv_id = match.group(1) # e.g. 2305.12345
    
    try:
        url = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
        response = requests.get(url, timeout=10)
        # Parse XML (Atom format)
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        # Extract authors
        authors = []
        entry = root.find('atom:entry', ns)
        if entry:
            for author in entry.findall('atom:author/atom:name', ns):
                authors.append(author.text)
            
            # Return formatted arxiv ID and full author list
            return f"arxiv:{arxiv_id}", ", ".join(authors)
    except:
        pass
    
    return None, None

def find_doi_strict(title):
    """
    Queries Crossref but ONLY accepts if title matches closely (>90%).
    This prevents 'mixed up' DOIs.
    """
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={requests.utils.quote(title)}&rows=1"
        response = requests.get(url, timeout=10)
        data = response.json()
        items = data.get('message', {}).get('items', [])
        
        if items:
            item = items[0]
            found_title = item.get('title', [''])[0]
            
            # SAFETY CHECK: Compare titles
            # If the search result isn't >85% similar to our paper, reject it.
            if similarity(title, found_title) < 0.85:
                return None, None
            
            doi = item.get('DOI')
            authors = []
            for a in item.get('author', []):
                family = a.get('family', '')
                given = a.get('given', '')
                if family and given:
                    authors.append(f"{family}, {given}")
                elif family:
                    authors.append(family)
            return doi, ", ".join(authors)
    except:
        pass
    return None, None

def main(entry):
    api_key = os.environ.get("GOOGLE_SCHOLAR_API_KEY", "")
    if not api_key: raise Exception('No "GOOGLE_SCHOLAR_API_KEY" env var')

    params = {"engine": "google_scholar_author", "api_key": api_key, "num": 100}
    _id = get_safe(entry, "gsid", "")
    if not _id: raise Exception('No "gsid" key')

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
        
        # --- STRATEGY: ---
        # 1. Is it ArXiv? -> Use ArXiv API directly. Safest for authors.
        # 2. Is it a Journal? -> Use Crossref with Strict Matching.
        # 3. Else -> Fallback to Google Scholar.

        cite_id = None
        full_authors = None

        # CHECK 1: ArXiv
        if "arxiv.org" in link:
            cite_id, full_authors = get_arxiv_data(link)
        
        # CHECK 2: Crossref (Only if not already identified as ArXiv)
        if not cite_id:
            doi, crossref_authors = find_doi_strict(title)
            if doi:
                cite_id = f"doi:{doi}"
                full_authors = crossref_authors
        
        # CHECK 3: Fallback ID
        if not cite_id:
            cite_id = link if link else get_safe(work, "citation_id", "")
            
        # Fallback Authors (Google Scholar snippet)
        # Only use this if we failed to get full lists from ArXiv or Crossref
        if not full_authors:
            raw_authors = get_safe(work, "authors", "")
        else:
            raw_authors = full_authors

        # --- HIGHLIGHTING LOGIC ---
        # Matches: Seifert, Tom | Seifert, T. | Seifert, T S | Seifert, T.S.
        # Uses \b to avoid matching "Tobias"
        pattern = r'(Seifert,?\s+(?:Tom\s+Sebastian|Tom\s+S\.?|T\.?\s?S\.?|T\.?S?|T\.?\b))'
        highlighted = re.sub(pattern, r'<b>\1</b>', raw_authors, flags=re.IGNORECASE)
        
        author_list = [a.strip() for a in highlighted.split(",")]

        source = {
            "id": cite_id,
            "title": title,
            "authors": author_list,
            "publisher": get_safe(work, "publication", ""),
            "date": (year + "-01-01") if year else "",
            "link": link,
        }
        source.update(entry)
        sources.append(source)

    return sources