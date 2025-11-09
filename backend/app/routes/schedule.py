from flask import Blueprint, request, send_file, jsonify
from ..services.schedule_visualizer import generate_schedule_png

schedule_bp = Blueprint("schedule", __name__)

@schedule_bp.route("/generate", methods=["POST"])
def generate_schedule():
    """
    Generate a schedule PNG from a list of courses.
    
    Expected JSON body:
    {
        "courses": [
            {
                "section": { ... section data ... },
                "catalog": { ... catalog data ... }
            },
            ...
        ]
    }
    
    Returns:
        PNG image file
    """
    try:
        data = request.get_json()
        if not data or "courses" not in data:
            return jsonify({"error": "Missing 'courses' field in request body"}), 400
        
        courses = data["courses"]
        if not isinstance(courses, list):
            return jsonify({"error": "'courses' must be a list"}), 400
        
        # Generate the schedule PNG
        img_buffer = generate_schedule_png(courses)
        
        # Return the image
        return send_file(
            img_buffer,
            mimetype="image/png",
            as_attachment=False,
            download_name="schedule.png"
        )
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
