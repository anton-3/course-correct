from bs4 import BeautifulSoup
import requests
import re
from collections import OrderedDict

STANDARD_FIELDS = [
    "course_code",
    "course_title",
    "Prerequisites",
    "Description",
    "Notes",
    "Credit Hours",
    "min_hours",
    "max_hours",
    "Min credits per semester",
    "Max credits per semester",
    "Max credits per degree",
    "Grading Option",
    "Offered",
    "Groups",
    "ACE",
    "Course and Laboratory Fee",
    "Experiential Learning",
    "Prerequisite for"
]

def clean_value(v):
    """Clean text value by removing special characters and extra whitespace."""
    return v.replace("\xa0", " ").strip().lstrip(":").strip()

def parse_course_block(block, search_query):
    """
    Parse a single course block div into a standardized course info dict.
    
    Args:
        block: BeautifulSoup element representing a courseblock div
        search_query: The original search query (used as fallback for course code)
    
    Returns:
        dict: Course information with standardized fields
    """
    # Try to determine a human-readable course title separate from the code
    def parse_title_parts(text: str, known_code: str) -> tuple[str, str]:
        """Given a full title string, extract (course_code, course_title).

        We prefer to use the known_code for robustness, but if the text
        includes a recognizable prefix, we extract accordingly.
        """
        t = clean_value(text)
        # If the string starts with the known code, strip it off
        if t.upper().startswith(known_code.upper()):
            remainder = t[len(known_code):].strip(" -:\u00a0")
            return known_code, clean_value(remainder)

        # Otherwise, try a regex like "SUBJ 123X  Title..."
        m = re.match(r"^([A-Z&]{2,}\s+\d+[A-Z]?)\s{1,}(.*)$", t)
        if m:
            parsed_code = clean_value(m.group(1))
            parsed_title = clean_value(m.group(2))
            return parsed_code, parsed_title

        # Fallback: return known code and entire string as title
        return known_code, t

    title_element = block.find("p", class_="courseblocktitle")
    if title_element:
        full_title = title_element.get_text(" ", strip=True)
        # Try to extract course code from the title
        m = re.match(r"^([A-Z&]{2,}\s+\d+[A-Z]?)\s{1,}(.*)$", full_title)
        if m:
            parsed_code, parsed_title = parse_title_parts(full_title, clean_value(m.group(1)))
        else:
            parsed_code, parsed_title = parse_title_parts(full_title, search_query)
    else:
        # Search results page often has the title in the enclosing article's <h3>
        parsed_code, parsed_title = search_query, ""
        article = block.find_parent("article")
        if article:
            h3 = article.find("h3")
            if h3:
                h3_text = h3.get_text(" ", strip=True)
                m = re.match(r"^([A-Z&]{2,}\s+\d+[A-Z]?)\s{1,}(.*)$", h3_text)
                if m:
                    parsed_code, parsed_title = parse_title_parts(h3_text, clean_value(m.group(1)))
                else:
                    parsed_code, parsed_title = parse_title_parts(h3_text, search_query)

    info = {
        "course_code": parsed_code or search_query,
        "course_title": parsed_title or ""
    }

    desc_elem = block.find("p", class_="courseblockdesc")
    if desc_elem:
        info["Description"] = clean_value(desc_elem.get_text(" ", strip=True))

    # Parse labeled fields
    for p in block.find_all("p"):
        strong = p.find("strong")
        if strong:
            label = strong.get_text(" ", strip=True).rstrip(":")
            value = p.get_text(" ", strip=True).replace(strong.get_text(" ", strip=True), "")
            info[label] = clean_value(value)

    # Parse Offered field from <em> tags
    offered_em = block.find("em", string=re.compile("FALL|SPR|SUMMER", re.I))
    if offered_em:
        info["Offered"] = offered_em.get_text(strip=True)

    # Convert Offered to list
    if "Offered" in info and info["Offered"]:
        info["Offered"] = info["Offered"].replace(" ", "").split("/")
    else:
        info["Offered"] = []

    # Parse Credit Hours min/max
    if "Credit Hours" in info:
        ch = clean_value(info["Credit Hours"])
        info["Credit Hours"] = ch
        nums = re.findall(r"[0-9]+(?:\.[0-9]+)?", ch)
        if len(nums) >= 2:
            info["min_hours"] = float(nums[0])
            info["max_hours"] = float(nums[1])
        elif len(nums) == 1:
            info["min_hours"] = info["max_hours"] = float(nums[0])

    # Standardize fields in a predictable order (explicitly preserve insertion order)
    final = OrderedDict()
    for field in STANDARD_FIELDS:
        final[field] = info.get(field, "")

    return final

def get_unl_course_info(course_code):
    """
    Fetch and parse course information from the UNL course catalog.
    Can search by specific course code (e.g., "CSCE 322") or by words/phrases.
        
    Returns:
        dict: Course information with standardized fields (if one course found)
        list: List of course information dicts (if multiple courses found)
        dict: Error dict with "error" key (if no courses found or error occurred)
    """
    query = course_code.replace(" ", "%20")
    url = f"https://catalog.unl.edu/search/?caturl=%2Fundergraduate&scontext=courses&search={query}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        blocks = soup.find_all("div", class_="courseblock")
        if not blocks:
            return {"error": f"No courses found for '{course_code}'"}

        # Parse all course blocks
        courses = [parse_course_block(block, course_code) for block in blocks]

        # Return single object if only one course, otherwise return array
        if len(courses) == 1:
            return courses[0]
        else:
            return courses

    except requests.RequestException as e:
        return {"error": f"Failed to fetch course info: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing course info: {str(e)}"}