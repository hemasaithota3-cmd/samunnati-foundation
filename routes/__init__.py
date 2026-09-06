def register_blueprints(app):
    from routes.public import public_bp
    from routes.guidance import guidance_bp
    from routes.mentor import mentor_bp
    from routes.volunteer import volunteer_bp
    from routes.auth import auth_bp
    from routes.admin import admin_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(guidance_bp)
    app.register_blueprint(mentor_bp)
    app.register_blueprint(volunteer_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
