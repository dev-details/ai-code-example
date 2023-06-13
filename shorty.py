import hashlib
import random
import string
import urllib.parse
from datetime import timedelta
import connexion
from redis import Redis


BASE_URL = "http://example.com/"

redis = Redis(host="redis", port=6379)


def create_app():
    app = connexion.FlaskApp(__name__, specification_dir="./")
    app.add_api("openapi.yaml")
    return app


def generate_short_code() -> str:
    """
    Generate a short code for the given URL.
    """
    # Generate a random 48 bit number and encode it in base62
    random_number = random.getrandbits(48)
    return encode_base_n(random_number, 62)


def encode_base_n(num, base):
    """
    Encode a number in the given base using digits from 0-9a-zA-Z.
    """
    digits = string.digits + string.ascii_letters
    if num == 0:
        return digits[0]
    arr = []
    while num:
        rem = num % base
        num //= base
        arr.append(digits[rem])
    arr.reverse()
    return "".join(arr)


def shorten_url(body):
    """
    Create a short URL for the given long URL.
    """
    url = body.get("url")
    if not url_valid(url):
        return {"error": "Invalid URL provided"}, 400

    # Check if the URL has been shortened before
    url_sha1 = hashlib.sha1(url.encode("utf-8")).digest()  # get bytes
    url_sha1_base62 = encode_base_n(int.from_bytes(url_sha1), 62)  # encode to base62
    long_url_key = f"long_url:{url_sha1_base62}"
    short_code = redis.get(long_url_key)

    if short_code:
        return {"url": f"{BASE_URL}{short_code.decode()}"}

    short_code = generate_short_code()
    short_code_key = f"code:{short_code}"

    # Save the short code - URL mapping
    redis.setex(short_code_key, timedelta(days=1), url)
    # Save the URL - short code mapping
    redis.setex(long_url_key, timedelta(days=1), short_code)

    return {"url": f"{BASE_URL}{short_code}"}


def redirect_to_url(short_code):
    """
    Redirect to the long URL corresponding to the given short code.
    """
    url = redis.get(f"code:{short_code}")
    if url:
        return None, 302, {"Location": url.decode("utf-8")}
    else:
        return (
            """
            <html>
                <head>
                    <title>404 Not Found</title>
                </head>
                <body>
                    <h1>404 Not Found</h1>
                    <p>The requested URL was not found on the server.</p>
                </body>
            </html>
        """,
            404,
        )


def url_valid(url: str) -> bool:
    # Validate url using urllib
    parsed_url = urllib.parse.urlparse(url)
    if parsed_url.scheme not in ["http", "https"]:
        return False
    if not parsed_url.netloc:
        return False

    return len(url) <= 2048


if __name__ == "__main__":
    app = create_app()
    app.run(port=8080)
