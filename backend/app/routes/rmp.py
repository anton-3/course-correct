from flask import Blueprint, jsonify, request
from ..services.rmp import RMPClient

rmp_bp = Blueprint("rmp", __name__)


@rmp_bp.get("/professor")
def professor_lookup():
    """GET /api/rmp/professor?school=School+Name&name=Professor+Name&num_reviews=40

    Returns a compact JSON summary for a professor using RateMyProfessor.
    Required query params: `school` and `name`
    Optional query params:
      - num_reviews: Number of recent reviews to fetch (default: 5, max: 100)

    Example response:
    {
      "name": "Full Name",
      "department": "Computer Science",
      "rating": 4.2,
      "difficulty": 3.1,
      "num_ratings": 42,
      "would_take_again": 87.5,
      "recent_comments": ["...", "..."],
    }
    """
    school = request.args.get("school")
    name = request.args.get("name")
    num_reviews = request.args.get("num_reviews", type=int, default=5)
    
    if not school or not name:
        return jsonify({"error": "Missing required query parameters 'school' and 'name'"}), 400
    
    if num_reviews < 1 or num_reviews > 100:
        return jsonify({"error": "num_reviews must be between 1 and 100"}), 400

    try:
        client = RMPClient()
        summary = client.get_professor_summary(school, name, comment_limit=num_reviews)
        # Inject audio trigger flag if professor matches Qing Hui
        if summary and isinstance(summary, dict):
            prof_name = str(summary.get("name", "")).strip().lower()
            # Use substring match to be robust if middle names / punctuation appear
            if "qing hui" in prof_name:
                summary["audio_trigger"] = "qing_hui"
        return jsonify(summary)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 502