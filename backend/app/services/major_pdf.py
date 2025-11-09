"""
Service for fetching UNL major requirement PDFs.
"""
from bs4 import BeautifulSoup
import requests
import re
from urllib.parse import urljoin, urlparse

MAJORS_PAGE_URL = "https://catalog.unl.edu/undergraduate/majors/"

def normalize_major_name(major: str) -> str:
    """
    Normalize major name for comparison.
    Removes extra whitespace, converts to lowercase.
    """
    return " ".join(major.strip().split()).lower()

def find_major_link(major_name: str):
    """
    Search the UNL majors page for a link to the specified major.
    
    Args:
        major_name (str): Name of the major to search for (e.g., "Anthropology", "Computer Science")
        
    Returns:
        dict: Contains 'url' if found, or 'error' if not found
    """
    try:
        r = requests.get(MAJORS_PAGE_URL, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        
        # The majors page has links to each major
        # We'll search for anchor tags whose text matches the major name
        normalized_search = normalize_major_name(major_name)
        
        # First pass: look for exact matches
        exact_match = None
        best_match = None
        best_match_score = 0
        
        # Find all links on the page
        for link in soup.find_all("a", href=True):
            link_text = link.get_text(strip=True)
            normalized_link = normalize_major_name(link_text)
            
            # Exact match is best
            if normalized_search == normalized_link:
                exact_match = {"url": urljoin(MAJORS_PAGE_URL, link["href"]), "matched_text": link_text}
                break
            
            # Check if the search term is in the link text
            if normalized_search in normalized_link:
                # Score by how close the match is (shorter is better)
                score = len(normalized_link) - len(normalized_search)
                if best_match is None or score < best_match_score:
                    best_match = {"url": urljoin(MAJORS_PAGE_URL, link["href"]), "matched_text": link_text}
                    best_match_score = score
        
        # Return exact match if found, otherwise best match
        if exact_match:
            return exact_match
        if best_match:
            return best_match
        
        return {"error": f"Major '{major_name}' not found on majors page"}
        
    except requests.RequestException as e:
        return {"error": f"Failed to fetch majors page: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing majors page: {str(e)}"}

def construct_pdf_url(major_page_url: str):
    """
    Given the major's page URL, construct the PDF URL.
    
    Pattern: If the page is at catalog.unl.edu/undergraduate/arts-sciences/anthropology/
    Then PDF is at catalog.unl.edu/undergraduate/arts-sciences/anthropology/anthropology.pdf
    
    Args:
        major_page_url (str): URL of the major's page
        
    Returns:
        str: URL of the PDF
    """
    # Parse the URL to get the path
    parsed = urlparse(major_page_url)
    path = parsed.path.rstrip("/")
    
    # Extract the last segment (the major name in the URL)
    segments = path.split("/")
    major_slug = segments[-1]
    
    # Construct PDF URL: same path + major_slug.pdf
    pdf_url = f"{parsed.scheme}://{parsed.netloc}{path}/{major_slug}.pdf"
    
    return pdf_url

def get_major_pdf_url(major_name: str):
    """
    Find the PDF URL for a given major.
    
    Args:
        major_name (str): Name of the major (e.g., "Computer Science", "Anthropology")
        
    Returns:
        dict: Contains 'pdf_url' and 'major_page_url' if successful, or 'error' if failed
    """
    # Step 1: Find the major's page URL
    result = find_major_link(major_name)
    
    if "error" in result:
        return result
    
    major_page_url = result["url"]
    
    # Step 2: Construct the PDF URL from the major page URL
    pdf_url = construct_pdf_url(major_page_url)
    
    return {
        "major_name": major_name,
        "matched_text": result.get("matched_text", ""),
        "major_page_url": major_page_url,
        "pdf_url": pdf_url
    }

def fetch_major_pdf(major_name: str):
    """
    Fetch the PDF content for a given major.
    
    Args:
        major_name (str): Name of the major
        
    Returns:
        dict: Contains 'content' (bytes) and 'pdf_url' if successful, or 'error' if failed
    """
    # Get the PDF URL
    result = get_major_pdf_url(major_name)
    
    if "error" in result:
        return result
    
    pdf_url = result["pdf_url"]
    
    # Fetch the PDF
    try:
        r = requests.get(pdf_url, timeout=15)
        r.raise_for_status()
        
        # Verify it's actually a PDF
        content_type = r.headers.get("Content-Type", "")
        if "pdf" not in content_type.lower():
            return {"error": f"URL did not return a PDF (Content-Type: {content_type})"}
        
        return {
            "content": r.content,
            "pdf_url": pdf_url,
            "major_name": major_name,
            "matched_text": result.get("matched_text", ""),
            "major_page_url": result.get("major_page_url", ""),
            "size_bytes": len(r.content)
        }
        
    except requests.RequestException as e:
        return {"error": f"Failed to fetch PDF from {pdf_url}: {str(e)}"}
    except Exception as e:
        return {"error": f"Error fetching PDF: {str(e)}"}
