import json
import math
import random
import io
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for server
import matplotlib.pyplot as plt

DAY_ORDER = ["M", "T", "W", "R", "F"]

# Pleasant readable pastel palette
PALETTE = [
    "#8ecae6", "#90be6d", "#f9c74f", "#f9844a", "#e56b6f",
    "#6ea4bf", "#8b6fb3", "#b56576", "#ffd6a5", "#6c757d"
]

def time_to_hour(t):
    """Convert HHMM → fractional hour. ex: 1230 → 12.5."""
    hour = t // 100
    minute = t % 100
    return hour + minute/60

def format_time_label(hour_float):
    """Convert fractional hour → HH:MM display label."""
    hr = int(hour_float)
    mn = int(round((hour_float - hr) * 60))
    return f"{hr:02d}:{mn:02d}"

def extract_course_blocks(course):
    """
    Extract schedule blocks from a combined course object with 'section' and 'catalog'.
    
    Args:
        course: Dict with 'section' (schedule data) and 'catalog' (course info)
    
    Returns:
        List of block dicts with day, start, end, label
    """
    section = course.get("section", {})
    catalog = course.get("catalog", {})
    
    course_code = catalog.get("course_code", section.get("course_code", ""))
    section_num = section.get("sectionNumber", "")
    
    # Get instructor name
    instructors = section.get("instructor", [])
    instructor = instructors[0].get("name", "") if instructors else ""
    
    meetings = section.get("meetings", [])

    # Get room from first meeting
    room = ""
    if meetings:
        building = meetings[0].get("buildingCode", "")
        roomnum = meetings[0].get("room", "")
        room = f"{building} {roomnum}".strip()

    blocks = []
    for m in meetings:
        start = time_to_hour(m["startTime"])
        end = time_to_hour(m["endTime"])
        for d in m.get("daysRaw", ""):
            if d in DAY_ORDER:
                blocks.append({
                    "day": d,
                    "start": start,
                    "end": end,
                    "label": f"{course_code} Sec {section_num}\n{instructor}\n{room}"
                })
    return blocks

def generate_schedule_png(course_json_list):
    """
    Generate a schedule PNG from a list of course objects.
    
    Args:
        course_json_list: List of dicts, each with 'section' and 'catalog' keys
    
    Returns:
        BytesIO object containing PNG image data
    """
    blocks = []
    for c in course_json_list:
        blocks.extend(extract_course_blocks(c))

    if not blocks:
        # Return empty schedule if no blocks
        fig, ax = plt.subplots(figsize=(11, 6))
        ax.text(0.5, 0.5, "No courses scheduled", 
                ha='center', va='center', fontsize=16)
        ax.axis('off')
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=200)
        plt.close()
        buf.seek(0)
        return buf

    # Assign color per unique class identity (course + section)
    course_ids = list({(b["label"].split("\n")[0]) for b in blocks})
    shuffled_palette = PALETTE.copy()
    random.shuffle(shuffled_palette)
    color_map = {cid: shuffled_palette[i % len(shuffled_palette)] for i, cid in enumerate(course_ids)}

    min_time = min(b["start"] for b in blocks)
    max_time = max(b["end"] for b in blocks)

    fig, ax = plt.subplots(figsize=(11, 6))
    ax.set_xlim(0, len(DAY_ORDER))
    ax.set_ylim(min_time, max_time)

    ax.set_xticks(range(len(DAY_ORDER)))
    ax.set_xticklabels(DAY_ORDER)

    # Y-axis 30-min ticks
    yticks = [min_time + i*0.5 for i in range(int((max_time-min_time)*2)+1)]
    ax.set_yticks(yticks)
    ax.set_yticklabels([format_time_label(t) for t in yticks])
    ax.invert_yaxis()

    # --------------------
    # DRAW GRID FIRST (behind blocks)
    # --------------------

    # Hour horizontal lines
    for t in range(math.floor(min_time), math.ceil(max_time) + 1):
        ax.axhline(t, color="#bbbbbb", linewidth=1.0, zorder=1)

    # Vertical day lines (grid)
    for i in range(len(DAY_ORDER) + 1):
        ax.axvline(i, color="#dddddd", linewidth=1.0, zorder=1)

    # --------------------
    # DRAW BLOCKS ON TOP
    # --------------------
    for b in blocks:
        x = DAY_ORDER.index(b["day"])
        y = b["start"]
        height = b["end"] - b["start"]

        course_id = b["label"].split("\n")[0]
        color = color_map[course_id]

        rect = plt.Rectangle(
            (x + 0.05, y),
            0.9,
            height,
            facecolor=color,
            edgecolor="black",
            linewidth=1.2,
            alpha=0.92,
            zorder=2  # Draw blocks on top of grid
        )
        ax.add_patch(rect)

        ax.text(
            x + 0.5,
            y + height/2,
            b["label"],
            ha='center',
            va='center',
            fontsize=8,
            color="black",
            zorder=3  # Draw text on top of everything
        )

    ax.set_ylabel("Time")
    ax.set_title("Course Schedule")
    plt.tight_layout()
    
    # Save to BytesIO buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=200)
    plt.close()
    buf.seek(0)
    
    return buf
