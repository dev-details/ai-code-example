from datetime import timedelta

import pytest
from urllib.parse import urlparse
from shorty import create_app
from fakeredis import FakeStrictRedis


@pytest.fixture(autouse=True)
def redis(monkeypatch):
    # monkeypatch `shorty.redis` with our fake redis
    redis = FakeStrictRedis()
    monkeypatch.setattr("shorty.redis", redis)
    yield
    # reset the redis
    redis.flushall()


@pytest.fixture()
def app():
    app = create_app()
    app.app.testing = True
    return app


# Create a fixture for test client
@pytest.fixture
def client(app):
    with app.app.test_client() as client:
        yield client


def test_shorten_valid_url(client):
    url = "https://www.very-long-url.com/"
    response = client.post("/shorten", json={"url": url})
    assert response.status_code == 200
    assert "url" in response.get_json()
    short_url = response.get_json()["url"]
    assert urlparse(short_url).netloc == "example.com"
    assert 8 <= len(urlparse(short_url).path.strip("/")) <= 9
    # then we use the short URL
    response = client.get(urlparse(short_url).path)
    assert response.status_code == 302
    assert response.headers["Location"] == url


def test_expired_short_url(client, freezer):
    url = "https://www.very-long-url.com/"
    # first we generate the short URL
    response = client.post("/shorten", json={"url": url})
    assert response.status_code == 200
    short_url = response.get_json()["url"]
    # then we time travel 24 hours into the future
    freezer.tick(delta=timedelta(hours=24, seconds=1))
    response = client.get(urlparse(short_url).path)
    assert response.status_code == 404


def test_shorten_invalid_url(client):
    url = "not a valid url"
    response = client.post("/shorten", json={"url": url})
    assert response.status_code == 400
    assert "error" in response.get_json()
    assert response.get_json()["error"] == "Invalid URL provided"


def test_idempotent_shorten(client):
    url = "https://www.very-long-url.com/"
    # first we generate the short URL
    response = client.post("/shorten", json={"url": url})
    assert response.status_code == 200
    short_url1 = response.get_json()["url"]
    # then we generate it again
    response = client.post("/shorten", json={"url": url})
    assert response.status_code == 200
    short_url2 = response.get_json()["url"]
    assert short_url1 == short_url2


def test_nonexistent_short_url(client):
    response = client.get("/nonexistent")
    assert response.status_code == 404
    assert "The requested URL was not found on the server." in response.get_data(
        as_text=True
    )


def test_different_urls_generate_different_short_urls(client):
    url1 = "https://www.very-long-url1.com/"
    url2 = "https://www.very-long-url2.com/"
    # generate the short URL for the first URL
    response = client.post("/shorten", json={"url": url1})
    assert response.status_code == 200
    short_url1 = response.get_json()["url"]
    # generate the short URL for the second URL
    response = client.post("/shorten", json={"url": url2})
    assert response.status_code == 200
    short_url2 = response.get_json()["url"]
    assert short_url1 != short_url2
