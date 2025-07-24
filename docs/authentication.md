# Authentication API

This document describes the authentication endpoints exposed by the API. All routes are prefixed with `/v1/auth` in production deployments.

## Registration

`POST /v1/auth/register`

Create a new user account. The body must include `email`, `password`, and optional `full_name`. Passwords must be at least eight characters and include upper and lower case letters, digits, and a special character.

## Email Verification

`GET /v1/auth/verify-email?token=<token>` *(not yet implemented)*

After registration, a verification email will be sent containing a link to this endpoint. Visiting the link marks the account as verified.

## Login

`POST /v1/auth/login`

Accepts form encoded fields `username` and `password`. On success returns an access token and refresh token. If multi-factor authentication (MFA) is enabled for the account the response status is `202` with header `X-MFA-Required: true` and you must complete the MFA challenge.

## MFA Challenge

`POST /v1/auth/mfa/verify`

Body must contain `email` and the MFA `code`. When verified, a new access token and refresh token are returned.

## Token Refresh

`POST /v1/auth/refresh`

Send a valid refresh token and receive a new access token. The refresh token itself may be rotated.

## Password Reset

`POST /v1/auth/password-reset/request`

Provide an email address and a password reset link will be delivered.

`POST /v1/auth/password-reset/confirm`

Submit the token from the reset email along with a new password to complete the reset.

## Environment Variables for Email Delivery

Configure these variables so the API can send verification and password reset emails:

```env
SMTP_HOST=<smtp-host>
SMTP_PORT=<smtp-port>
SMTP_USERNAME=<smtp-user>
SMTP_PASSWORD=<smtp-pass>
EMAIL_FROM=no-reply@example.com
```

## Using Refresh Tokens with HTTP-only Cookies

When logging in, store the returned `refresh_token` in an HTTP-only cookie:

```bash
# Login and capture refresh token
curl -X POST http://localhost:8000/v1/auth/login \
     -d 'username=user@example.com&password=secret' \
     -c cookies.txt
```

Save the token from the response JSON in an `HttpOnly` cookie named `refresh_token`. Subsequent refresh calls send the cookie instead of the token in the body:

```bash
# Example of sending refresh token via cookie
curl -X POST http://localhost:8000/v1/auth/refresh \
     -b cookies.txt
```

The backend will read the cookie and issue a new access token.
