# Security Policy

## 🛡️ Supported Versions

| Version | Supported |
| :--- | :--- |
| `v1.0.x` | ✅ Supported |
| `< 1.0.0` | ❌ Unsupported |

---

## 🚨 Reporting a Vulnerability

We take the security of Enterprise NIDS seriously. If you discover a security vulnerability (such as a flaw in JWT handling, RBAC bypass, packet injection, or secret leakage), please **DO NOT open a public issue**.

### Reporting Process:
1. Email security vulnerability reports privately to `security@enterprise-nids.local`.
2. Include:
   - Type of issue (e.g., Auth Bypass, Remote Code Execution, Memory Leak).
   - Step-by-step proof of concept (PoC).
   - Potential impact on production deployments.
3. You will receive an acknowledgment within **24 hours**, and a mitigation timeline within **72 hours**.

---

## 🔒 Security Architecture Highlights

- **JWT Authentication**: Signed with HMAC-SHA256 & 256-bit secret keys.
- **RBAC**: 5-Tier Permission Enforcement Matrix (`Administrator`, `SOC Analyst`, `Security Engineer`, `Read Only`, `Guest`).
- **Input Sanitization**: Pydantic Schema Validation on all incoming API request payloads.
- **Rate Limiting**: Sliding Token-Bucket Rate Limiter protecting public endpoints.
- **Security Headers**: OWASP recommended HTTP response headers (`X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `X-XSS-Protection: 1; mode=block`).
