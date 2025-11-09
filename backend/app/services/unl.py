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

def get_unl_course_info(dept: str, code: str):
    """
    Fetch and parse course information from the UNL course catalog.
    
    Args:
        dept (str): Department code (e.g., "CSCE")
        code (str): Course number (e.g., "481")
        
    Returns:
        dict: Course information with standardized fields
    """
    course_code = f"{dept} {code}"
    query = f"{dept}%20{code}"
    url = f"https://catalog.unl.edu/search/?caturl=%2Fundergraduate&scontext=courses&search={query}"

    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        block = soup.find("div", class_="courseblock")
        if block is None:
            return {"error": f"Course {course_code} not found"}

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
            parsed_code, parsed_title = parse_title_parts(full_title, course_code)
        else:
            # Search results page often has the title in the enclosing article's <h3>
            parsed_code, parsed_title = course_code, ""
            article = block.find_parent("article")
            if article:
                h3 = article.find("h3")
                if h3:
                    parsed_code, parsed_title = parse_title_parts(h3.get_text(" ", strip=True), course_code)

        info = {
            "course_code": parsed_code or course_code,
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

    except requests.RequestException as e:
        return {"error": f"Failed to fetch course info: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing course info: {str(e)}"}