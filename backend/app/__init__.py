from flask import Flask
from flask_cors import CORS
from .config import load_config


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Load configuration
    app.config.update(load_config())
    # Preserve key order in JSON responses (Flask defaults to sorting keys)
    try:
        # Flask 2 style
        app.config["JSON_SORT_KEYS"] = False
        # Flask 3 JSON provider also respects this attribute
        if hasattr(app, "json") and hasattr(app.json, "sort_keys"):
            app.json.sort_keys = False
    except Exception:
        # Non-fatal; best-effort to preserve order
        pass

    # Register blueprints
    from .routes.health import health_bp
    from .routes.elevenlabs import elevenlabs_bp
    from .routes.conversation import conversation_bp
    from .routes.rmp import rmp_bp
    from .routes.agent import agent_bp
    from .routes.unl import unl_routes
    from .routes.schedule import schedule_bp
    from .routes.major import major_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(elevenlabs_bp, url_prefix="/api/elevenlabs")
    app.register_blueprint(conversation_bp, url_prefix="/api/conversation")
    app.register_blueprint(rmp_bp, url_prefix="/api/rmp")
    app.register_blueprint(agent_bp, url_prefix="/api/agent")
    app.register_blueprint(unl_routes, url_prefix="/api/unl")
    app.register_blueprint(schedule_bp, url_prefix="/api/schedule")
    app.register_blueprint(major_bp, url_prefix="/api/major")

    @app.get("/")
    def root():
        return {"name": "bananadvisor-backend", "status": "ok"}

    return app
