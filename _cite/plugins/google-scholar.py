import os
import re
import requests
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse
from difflib import SequenceMatcher
from serpapi import GoogleSearch
from util import *

# identify ourselves to Crossref/arXiv; Crossref routes requests with a contact
# address to its more reliable "polite" pool (anonymous requests often time out)
# (set the CITE_CONTACT_EMAIL env var / repo variable to opt in)
CONTACT = os.environ.get("CITE_CONTACT_EMAIL", "").strip()
HEADERS = {"User-Agent": "lab-website-cite/1.0" + (f" (mailto:{CONTACT})" if CONTACT else "")}

# optional manual fixes for individual papers, keyed by title (see file header)
OVERRIDES_FILE = "_data/citation-overrides.yaml"


def normalize_title(text):
    """
    Lowercase and strip markup/punctuation so titles from Google Scholar,
    Crossref and arXiv compare fairly (e.g. "<i>Ab</i> initio", "N\\'eel").
    """
    if not text: return ""
    text = re.sub(r"<[^>]+>", " ", str(text))
    text = re.sub(r"\\[a-zA-Z]+|\\.", "", text)
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return text.strip()


def similarity(a, b):
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio()


def http_get(url, params=None, timeout=20, tries=3):
    """
    GET with a contact header and a few retries on timeouts / rate limits.
    Returns the response, or None if every attempt failed.
    """
    for attempt in range(tries):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=timeout)
            if response.status_code == 200:
                return response
            if response.status_code not in (429, 500, 502, 503, 504):
                return None
        except requests.RequestException:
            pass
        time.sleep(2 * (attempt + 1))
    return None


def load_overrides():
    """
    Load manual per-paper fixes. Returns {normalized title: override dict}.
    """
    try:
        data = load_data(OVERRIDES_FILE)
    except Exception:
        return {}
    overrides = {}
    for item in data if list_of_dicts(data) else []:
        title = normalize_title(item.get("title", ""))
        if title:
            overrides[title] = item
    return overrides


def short_link_label(url):
    """
    Short human-readable label for a plain URL, e.g. "pubs.rsc.org".
    """
    host = urlparse(url).netloc.lower()
    if host.startswith("www."): host = host[4:]
    if "scholar.google" in host: return "Google Scholar"
    return host or "Link"

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
        url = f'https://export.arxiv.org/api/query?search_query=all:{requests.utils.quote(clean_query)}&max_results=1'
        response = http_get(url)
        if response is None: return None
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom', 'arxiv': 'http://arxiv.org/schemas/atom'}
        
        entry = root.find('atom:entry', ns)
        if entry is not None:
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

def find_doi_strict(title, allow_preprint=True):
    """
    Look a title up on Crossref and return (doi, authors, journal, year) for the
    best-matching record, or None. Checks the top few hits rather than only the
    first, since conference abstracts/errata often outrank the actual paper.
    With allow_preprint=False, arXiv DOIs and other preprints are skipped.
    """
    if not title or len(title) < 5: return None
    response = http_get(
        "https://api.crossref.org/works",
        params={
            "query.bibliographic": title,
            "rows": 5,
            "select": "DOI,title,subtitle,container-title,author,published-print,published-online,created,type",
            **({"mailto": CONTACT} if CONTACT else {}),
        },
    )
    if response is None: return None
    try:
        items = response.json().get("message", {}).get("items", [])
    except ValueError:
        return None

    best, best_score = None, 0
    for item in items:
        doi = item.get("DOI", "")
        if not allow_preprint and (
            item.get("type") == "posted-content" or doi.lower().startswith("10.48550/")
        ):
            continue
        found = (item.get("title") or [""])[0]
        subtitle = (item.get("subtitle") or [""])[0]
        score = max(similarity(title, found), similarity(title, f"{found}: {subtitle}"))
        if score > best_score:
            best, best_score = item, score

    if not best or best_score < 0.85:
        return None

    doi = best.get("DOI")
    journal = (best.get("container-title") or [""])[0]

    authors = []
    for a in best.get("author", []):
        family = a.get("family", "")
        given = a.get("given", "")
        if family and given:
            authors.append(f"{family}, {given}")
        elif family:
            authors.append(family)

    year = ""
    for key in ("published-print", "published-online", "created"):
        try:
            year = str(best[key]["date-parts"][0][0])
            break
        except (KeyError, IndexError, TypeError):
            continue

    return doi, ", ".join(authors), journal, year


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
    overrides = load_overrides()

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
                # arXiv often lags behind publication: ask Crossref for the
                # journal DOI before falling back to the preprint
                journal_doi = find_doi_strict(ax_title, allow_preprint=False)
                if journal_doi:
                    ax_doi = journal_doi[0]
                    cite_id = f"doi:{ax_doi}"
                    final_link = f"https://doi.org/{ax_doi}"
                    if is_valid_journal(journal_doi[2]):
                        final_pub = journal_doi[2]
            if not ax_doi:
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
        # No DOI/arXiv id found. Leave the id empty (Manubot can't cite a bare
        # web page anyway) and show a short label instead of the full URL.
        link_label = ""
        if not cite_id:
            gs_link = get_safe(work, "link", "")
            if gs_link and "scholar.google" not in gs_link and gs_link.startswith("http"):
                final_link = gs_link
            else:
                final_link = "https://scholar.google.com/scholar?q=" + requests.utils.quote(f'"{gs_title}"')
            link_label = short_link_label(final_link)

        # --- D. Manual overrides (_data/citation-overrides.yaml) ---
        override = overrides.get(normalize_title(gs_title)) or overrides.get(normalize_title(final_title))
        if override:
            if override.get("remove"):
                continue
            if override.get("doi"):
                doi = str(override["doi"]).strip()
                doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi, flags=re.IGNORECASE)
                cite_id = f"doi:{doi}"
                final_link = f"https://doi.org/{doi}"
                link_label = ""
            elif override.get("link"):
                cite_id = None
                final_link = str(override["link"]).strip()
                link_label = override.get("label") or short_link_label(final_link)
            for key in ("title", "publisher", "year"):
                if override.get(key):
                    if key == "title": final_title = override[key]
                    if key == "publisher": final_pub = override[key]
                    if key == "year": final_year = str(override[key])

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
            "id": cite_id or "",
            "title": final_title,
            "authors": author_list,
            "publisher": clean_pub_str,
            "date": sortable_date,
            "year": final_year,
            "link": final_link,
        }
        if link_label:
            source["link_label"] = link_label
        source.update(entry)
        sources.append(source)

    # --- 6. FINAL SORT ---
    sources.sort(key=lambda x: str(x.get('year', '0')), reverse=True)

    return sources