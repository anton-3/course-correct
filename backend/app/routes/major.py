"""
Routes for fetching UNL major requirement PDFs.
"""
from flask import Blueprint, request, jsonify, send_file
from io import BytesIO
from app.services.major_pdf import get_major_pdf_url, fetch_major_pdf

major_bp = Blueprint("major", __name__)

@major_bp.route("/pdf", methods=["GET"])
def get_major_pdf():
    """
    Get the PDF for a major.
    
    Query Parameters:
        major (str): Name of the major (e.g., "Computer Science", "Anthropology")
        url_only (bool): If true, return only the PDF URL without fetching the file
        
    Returns:
        PDF file or JSON with URL information
    """
    major_name = request.args.get("major")
    
    if not major_name:
        return jsonify({"error": "Missing 'major' parameter"}), 400
    
    # Check if user only wants the URL
    url_only = request.args.get("url_only", "false").lower() == "true"
    
    if url_only:
        # Just return the URL information
        result = get_major_pdf_url(major_name)
        if "error" in result:
            return jsonify(result), 404
        return jsonify(result), 200
    
    # Fetch the actual PDF
    result = fetch_major_pdf(major_name)
    
    if "error" in result:
        return jsonify(result), 404
    
    # Return the PDF file
    pdf_buffer = BytesIO(result["content"])
    pdf_buffer.seek(0)
    
    # Sanitize filename
    safe_filename = major_name.replace(" ", "_").replace("/", "-")
    filename = f"{safe_filename}.pdf"
    
    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename
    )

@major_bp.route("/search", methods=["GET"])
def search_major():
    """
    Search for a major and return its URL information.
    
    Query Parameters:
        major (str): Name of the major to search for
        
    Returns:
        JSON with major page URL and PDF URL
    """
    major_name = request.args.get("major")
    
    if not major_name:
        return jsonify({"error": "Missing 'major' parameter"}), 400
    
    result = get_major_pdf_url(major_name)
    
    if "error" in result:
        return jsonify(result), 404
    
    return jsonify(result), 200
