import os
import bcrypt
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from jose import jwt

# Load .env here too, not just in database.py. SECRET_KEY is read at import time,
# so without this the module only works when something else (database.py) happened
# to be imported first — any script that reaches auth directly would die with a
# misleading "SECRET_KEY not set" despite .env being correct. load_dotenv() is
# idempotent and won't override variables already set in the environment.
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable not set")  # crash loud at startup rather than sign tokens with no key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 12 #  12 hours duration before having to log back in, refresh token will be added later


def hash_password(plain: str) -> str: #hashing
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()  # gensalt() makes each hash unique even for identical passwords


def verify_password(plain: str, hashed: str) -> bool: #compares users password to hased one
    return bcrypt.checkpw(plain.encode(), hashed.encode())  # bcrypt re-derives the salt from the stored hash to compare


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),  # "subject" = who the token belongs to (stringified, jwt convention)
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),  # expiry, jose rejects the token automatically once passed
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)  # sign the claims into a token string


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # verify signature + expiry, raises JWTError if bad/expired
