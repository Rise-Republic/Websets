# WorkOS AuthKit Security Implementation

## Overview

This document outlines the security measures implemented for WorkOS AuthKit integration in the Websets application.

## Security Features

1. **Encrypted Session Cookies**
   - HTTP-only, secure cookies with SameSite=Lax
   - 14-day expiration with automatic renewal
   - No raw tokens exposed to frontend

2. **PKCE + State Validation**
   - CSRF protection via state parameter
   - 5-minute expiration on authorization codes
   - State stored in secure HTTP-only cookie

3. **Session Validation**
   - Global middleware for protected routes
   - Per-route dependency injection option
   - Automatic session verification

4. **MFA & Passkeys**
   - Optional MFA via `WORKOS_ENFORCE_MFA` environment variable
   - Passkey support enabled by default
   - Step-up authentication for sensitive operations

## Critical Security Credentials

### WORKOS_COOKIE_PASSWORD

**⚠️ CRITICAL: This 32-byte key must be securely stored in production Vault**

```bash
# Generate a new key (do this ONCE per environment)
head -c 32 /dev/urandom | base64
```

Current development value: `yvHkj2U4tkv+oYGZon1EDfQVtbb4ro9cabdEAV9YH9A=`

### Required Environment Variables

| Variable | Purpose | Storage |
|----------|---------|---------|
| `WORKOS_API_KEY` | API authentication | Vault |
| `WORKOS_CLIENT_ID` | Client identification | Vault |
| `WORKOS_COOKIE_PASSWORD` | Session encryption | Vault |
| `WORKOS_WEBHOOK_SECRET` | Webhook verification | Vault |
| `WORKOS_ENFORCE_MFA` | Optional MFA toggle | Environment |

## Deployment Checklist

1. [ ] Generate new `WORKOS_COOKIE_PASSWORD` for production
2. [ ] Store in production Vault instance
3. [ ] Configure exact redirect URIs in WorkOS dashboard
4. [ ] Set up webhook endpoints with signature verification
5. [ ] Implement quarterly API key rotation

## Security Best Practices

- Never expose raw tokens in JSON responses or localStorage
- Use HTTP-only cookies for all authentication data
- Implement proper CSRF protection for state-changing operations
- Enable MFA for administrative accounts
- Rotate API keys quarterly

## Code References

- Session middleware: `/app/api/v1/workos_auth.py`
- FastAPI integration: `/app/main.py`
- Vault secrets: `/vault_secrets_template.json`

## Additional Resources

- [WorkOS AuthKit Documentation](https://workos.com/docs/authkit)
- [OWASP Authentication Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
