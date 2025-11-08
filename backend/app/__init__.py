from flask import Flask
from flask_cors import CORS
from .config import load_config


def create_app():
    app = Flask(__name__)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Load configuration
    app.config.update(load_config())

    # Register blueprints
    from .routes.health import health_bp
    from .routes.elevenlabs import elevenlabs_bp
    from .routes.conversation import conversation_bp
    from .routes.rmp import rmp_bp
    # Agent blueprint may fail if Google GenAI dependencies/credentials are missing.
    # Import defensively so the rest of the app (e.g., RMP + ElevenLabs) still works.
    try:
        from .routes.agent import agent_bp  # type: ignore
    except Exception as e:  # broad catch: missing deps or config
        agent_bp = None
        app.logger.warning(f"Agent blueprint disabled: {e}")

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(elevenlabs_bp, url_prefix="/api/elevenlabs")
    app.register_blueprint(conversation_bp, url_prefix="/api/conversation")
    app.register_blueprint(rmp_bp, url_prefix="/api/rmp")
    if agent_bp is not None:
        app.register_blueprint(agent_bp, url_prefix="/api/agent")

    @app.get("/")
    def root():
        return {"name": "bananadvisor-backend", "status": "ok"}

    return app
