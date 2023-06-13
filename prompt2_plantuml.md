Write a PlantUML sequence diagram for the API interactions of the design below.

- Use descriptive aliases. Don't use one-letter aliases.
- Activate/deactivate each component in the sequence diagram when appropriate
- Separate use cases with section titles
- Use "actor" instead of `participant` for the user
- Include each record of the data model that we need to store

# URL Shortening Service

## Context

This service provides APIs that take long URLs and provide a short URL suitable
for easy sharing.

## Functional Requirements

- The JSON API should allow users to submit a long URL and receive a shortened
  URL in return.
- When visiting the shortened URL, the visitor will be redirected to the long
  URL.
- When visiting a short URL that is not found or has expired, the response
  should be an HTML error page with an
  appropriate HTTP status code and an error message. The error page should
  provide a user-friendly display.
- Short URLs are only valid for 24 hours. After the 24-hour validity window, a
  new short URL should be generated for the
  same long URL.
- The JSON API must be idempotent -- submitting the same long URL will result in
  the same short URL for the 24-hour
  validity window.
- A short code URL should not be repeated for ~10 years (Data does not need to
  be stored this long, but it should be
  statistically unlikely to duplicate a short code for this time period.)
- The short URL "short code" should be less than 10 characters.

## Non-functional requirements

- Be able to handle generating and storing ~200,000 short URLs a day and up to
  2,000,000 short URLs in a day during a
  10x spike in URL generation.
- Use minimal memory, up to 2GB.
- Response times for URL access (read APIs) should be under 100 ms.
- Response times for write APIs should be under 200 ms.
- Be able to handle 1,000,000 redirects per URL per day.

## Use Cases

- User submits a long URL and receives a short URL in response.
- User visits the short URL and gets redirected to the original long URL.
- User attempts to access an expired short URL and receives an appropriate
  response.
- User submits an invalid long URL and gets an error response.
- User submits the same long URL multiple times and receives the same short URL
  within the 24-hour duration.

## Exclusions

- Rate limiting: This service does not need to handle rate limiting as it will
  be handled by the API Gateway.
- Authentication: This service does not need to handle authentication as it will
  be handled by the API Gateway.
- Security: The API should protect against standard injection attacks, but
  security measures such as authentication and
  WAF will be handled separately.
- Deletion of URLs is not supported.

## Implementation Details

- Python 3 Connexion library for API service.
- Redis for backend storage (single instance setup initially, scale up as
  needed).

### Short Codes

- A random 48 bit number -- This gives us a huge number of possible codes (~ 141
  trillion), which makes the probability
  of a collision in the next 10 years extremely low, even at our maximum
  estimated rate of code generation.
- Base62 encode the 48 bit number -- 8 character long short code.

### Data Model

We will store data in Redis as strings.

#### Short code to long URL mapping

Key: `{short_code}`
Value: `{long_url}`
TTL: 24 hours

#### Long URL to short code mapping

Key: `{url_sha1_base62}`
Value: `{short_code}`
TTL: 24 hours

### Input Validation

- URLs should be limited to 2048 characters.
- URLs must follow standards and be validated for correctness.

## Observability

### Metrics

- Metrics use OpenTelemetry.
- Track each time a URL is visited. Only the `short_code` and `timestamp` should
  be recorded.

### Logging

- [ECS JSON format](https://www.elastic.co/guide/en/ecs/current/ecs-reference.html).
- Generate a log when a URL is created.
- Generate a log on errors, except for 404 errors.

## Privacy and Security

- The full URL must not be logged.
- IP addresses must not be logged.
- The API should protect against standard injection attacks.
- Additional security measures such as authentication and WAF will be handled
  separately.

## Deployment

- The application will be containerized for deployment.
- Scalability requirements have been described in the non-functional
  requirements and this will use our standard
  deployment. Once we measure usage, we will adjust the deployment plans as
  needed.

## API

The API has the following endpoints:

1. `/shorten` - A `POST` endpoint to shorten a long URL. It accepts a JSON
   payload with a `url` property containing the
   long URL. The response includes a `url` property with the generated short
   URL. Invalid URLs result in a `400` error
   response.
2. `/{short_code}` - A `GET` endpoint to redirect users to the original long URL
   based on the provided short code. It
   returns a `302` status code for successful redirection and an HTML error page
   with a `404` status code if the short
   URL is not found.

## Style Guide

Our organization follows these principles for development.

- DRY
- SOLID
- TDD

Our company follows these coding styles and best practices:

- Use Python `black` formatting.
- Use Python type hints.
- Pytest for testing.
- Testing:
    - All business use cases should be covered in the tests.
    - Focus testing on business case functional testing to test at API
      boundaries such as REST APIs -- not class-level
      tests.
    - For fake data use "example" in the name. "test" must only be used for the
      test names themselves.
    - If monkey-patching or other dependency injection is necessary, only do so
      in pytest fixtures -- no dependency
      injection in tests themselves.
    - Use testing analogs for external dependencies like databases. Do not use
      test analogs for our own code.
    - Testing analogs should function the same as the libraries and services
      they mimic. Only implement as much analog
      functionality as needed for the test.
    - For test analogs, use "fake" in the name.
