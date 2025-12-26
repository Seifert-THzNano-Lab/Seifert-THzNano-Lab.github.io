import os
import re
import requests
import xml.etree.ElementTree as ET
from difflib import SequenceMatcher
from serpapi import GoogleSearch
from util import *

def similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def clean_journal(text):
    """
    Cleaning strictly for DISPLAY purposes.
    Removes patterns like 'Vol. 12', 'pp. 100-200', and ', 2023'.
    """
    if not text: return ""
    text = re.sub(r'\d+\s*\(\d+\).*', '', text)
    text = re.sub(r'Vol\.\s*\d+.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'pp\.\s*\d+.*', '', text, flags=re.IGNORECASE)
    # Remove year at the end (e.g., ", 2023")
    text = re.sub(r',\s*\d{4}.*', '', text)
    text = re.sub(r'[\d,-]+$', '', text)
    return text.strip()

def extract_year_safe(text):
    """
    Finds the first 4-digit year (19xx or 20xx) in a string.
    """
    if not text: return ""
    match = re.search(r'\b(19|20)\d{2}\b', str(text))
    if match:
        return match.group(0)
    return ""

def is_valid_journal(name):
    """
    Returns True if the name looks like a real journal (not empty, not just 'arXiv').
    """
    if not name: return False
    lower_name = name.lower()
    if "arxiv" in lower_name: return False
    if "biorxiv" in lower_name: return False
    if "chemrxiv" in lower_name: return False
    return True

def search_arxiv_by_title(title):
    if not title or len(title) < 5: return None
    clean_query = re.sub(r'[^a-zA-Z0-9\s]', '', title)
    
    try:
        url = f'http://export.arxiv.org/api/query?search_query=all:{requests.utils.quote(clean_query)}&max_results=1'
        response = requests.get(url, timeout=5)
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        
        entry = root.find('atom:entry', ns)
        if entry:
            found_title = entry.find('atom:title', ns).text.strip()
            found_title = re.sub(r'\s+', ' ', found_title)
            
            if similarity(title, found_title) > 0.85:
                id_url = entry.find('atom:id', ns).text
                arxiv_id = id_url.split('/abs/')[-1].split('v')[0]
                
                authors = []
                for author in entry.findall('atom:author/atom:name', ns):
                    name_parts = author.text.strip().split()
                    if len(name_parts) > 1:
                        authors.append(f"{name_parts[-1]}, {' '.join(name_parts[:-1])}")
                    else:
                        authors.append(author.text)
                
                doi = None
                doi_tag = entry.find('arxiv:doi', ns)
                if doi_tag is not None: doi = doi_tag.text

                journal_ref = ""
                j_tag = entry.find('arxiv:journal_ref', ns)
                if j_tag is not None: journal_ref = j_tag.text
                
                published = entry.find('atom:published', ns).text
                year = published[:4] if published else ""

                return arxiv_id, ", ".join(authors), found_title, doi, journal_ref, year
    except:
        pass
    return None

def find_doi_strict(title):
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={requests.utils.quote(title)}&rows=1"
        response = requests.get(url, timeout=5)
        data = response.json()
        items = data.get('message', {}).get('items', [])
        
        if items:
            item = items[0]
            found_title = item.get('title', [''])[0]
            if similarity(title, found_title) < 0.85:
                return None
            
            doi = item.get('DOI')
            journal = item.get('container-title', [''])[0]
            
            authors = []
            for a in item.get('author', []):
                family = a.get('family', '')
                given = a.get('given', '')
                if family and given:
                    authors.append(f"{family}, {given}")
                elif family:
                    authors.append(family)
            
            year = ""
            if 'published-print' in item:
                year = str(item['published-print']['date-parts'][0][0])
            elif 'published-online' in item:
                year = str(item['published-online']['date-parts'][0][0])
            elif 'created' in item:
                year = str(item['created']['date-parts'][0][0])

            return doi, ", ".join(authors), journal, year
    except:
        pass
    return None

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
        # --- 1. YEAR EXTRACTION ---
        raw_year = str(work.get("year", "")).strip()
        if raw_year == "None": raw_year = ""
        
        pub_year = extract_year_safe(work.get("publication", ""))
        snippet_year = extract_year_safe(work.get("snippet", ""))

        final_year = raw_year or pub_year or snippet_year

        # --- 2. SETUP BASICS ---
        gs_title = get_safe(work, "title", "")
        cite_id = None
        final_authors = get_safe(work, "authors", "")
        final_title = gs_title
        
        # Start with Google Scholar's publisher string
        final_pub = get_safe(work, "publication", "")
        
        final_link = "" 
        
        # --- 3. EXTERNAL ENRICHMENT ---
        
        # --- A. Check ArXiv ---
        arxiv_data = search_arxiv_by_title(gs_title)
        if arxiv_data:
            ax_id, ax_auth, ax_title, ax_doi, ax_journal, ax_year = arxiv_data
            
            # ArXiv is often more up-to-date with authors/titles
            final_authors = ax_auth
            final_title = ax_title 
            if ax_year and len(ax_year) == 4: final_year = ax_year
            
            if ax_doi:
                # If ArXiv knows the DOI, it's definitely published.
                cite_id = f"doi:{ax_doi}"
                final_link = f"https://doi.org/{ax_doi}"
                # If ArXiv metadata has a real journal ref, use it.
                if is_valid_journal(ax_journal):
                    final_pub = ax_journal
                # Else: Keep the Google Scholar journal we already had (don't overwrite with 'arXiv')
            else:
                # No DOI yet (Preprint status)
                cite_id = f"arxiv:{ax_id}"
                final_link = f"https://arxiv.org/abs/{ax_id}"
                
                # --- CRITICAL FIX FOR JOURNAL NAME ---
                # Only overwrite publisher with "arXiv" if we DON'T have a real journal yet.
                if not is_valid_journal(final_pub):
                    final_pub = "arXiv"
                # If final_pub was "Physical Review B", we KEEP it, even though we link to ArXiv.

        # --- B. Check Crossref (if no ID yet) ---
        if not cite_id:
            crossref_data = find_doi_strict(gs_title)
            if crossref_data:
                doi, doi_auth, doi_jour, cr_year = crossref_data
                cite_id = f"doi:{doi}"
                final_authors = doi_auth
                final_link = f"https://doi.org/{doi}"
                
                # Crossref usually has the official journal name -> Priority 1
                if is_valid_journal(doi_jour):
                    final_pub = doi_jour
                    
                if cr_year and len(cr_year) == 4: final_year = cr_year

        # --- C. Fallback Link ---
        if not cite_id:
            gs_link = get_safe(work, "link", "")
            if gs_link and "scholar.google" not in gs_link and gs_link.startswith("http"):
                 cite_id = f"url:{gs_link}"
                 final_link = gs_link
            else:
                 safe_search = f"https://google.com/search?q={requests.utils.quote(gs_title)}"
                 cite_id = f"url:{safe_search}"
                 final_link = safe_search

        # --- 4. FORMATTING ---
        clean_pub_str = clean_journal(final_pub)
        if final_year:
            clean_pub_str = f"{clean_pub_str} ({final_year})"
        
        # Highlight Authors
        p1 = r'(Seifert,?\s+(?:Tom\s+Sebastian|Tom\s+S\.?|'
        p2 = r'T\.?\s?S\.?|T\.?S?|T\.?\b))'
        pattern = p1 + p2
        highlighted = re.sub(pattern, r'<b>\1</b>', final_authors, flags=re.IGNORECASE)
        author_list = [a.strip() for a in highlighted.split(",")]

        # --- 5. DATE FIX ---
        sortable_date = f"{final_year}-01-01" if final_year else ""

        source = {
            "id": cite_id,
            "title": final_title,
            "authors": author_list,
            "publisher": clean_pub_str,
            "date": sortable_date,
            "year": final_year,
            "link": final_link,
        }
        source.update(entry)
        sources.append(source)

    # --- 6. FINAL SORT ---
    sources.sort(key=lambda x: str(x.get('year', '0')), reverse=True)

    return sources