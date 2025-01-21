from HardwareTester.models.user_models import Token
from flask_wtf.csrf import generate_csrf
from HardwareTester.extensions import db
from datetime import datetime, timedelta

def get_token(user_id=None, expiration_duration=3600):
    """
    Retrieve or create a persistent CSRF token for a user.
    
    :param user_id: ID of the user for whom the token is being generated.
    :param expiration_duration: Duration (in seconds) for the token to remain valid. Defaults to 1 hour.
    :return: CSRF token string.
    """
    if not user_id:
        raise ValueError("User ID must be provided to generate or retrieve a token.")

    # Query the existing token for the user
    token = Token.query.filter_by(user_id=user_id).first()

    # Check if the token exists and is valid
    if token and token.expiration > datetime.utcnow():
        return token.token

    # Generate a new token if none exists or the token is expired
    csrf_token = generate_csrf()
    expiration = datetime.utcnow() + timedelta(seconds=expiration_duration)

    if token:  # Update existing token
        token.token = csrf_token
        token.expiration = expiration
    else:  # Create a new token
        token = Token(user_id=user_id, token=csrf_token, expiration=expiration)
        db.session.add(token)

    # Commit changes to the database
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise RuntimeError(f"Failed to save token: {str(e)}")

    return token.token
