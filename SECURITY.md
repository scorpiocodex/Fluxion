# Security Policy

## Supported Versions

| Version | Supported |
|:--------|:----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub Issues.**

Report security vulnerabilities privately via email:

**scorpiocodex0@gmail.com**

Include:
- A description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes (optional)

You will receive an acknowledgment within **48 hours** and a full response within **7 days**.

## Security Features

Fluxion implements the following security controls:

### TLS / Certificate Security

- **TLS Deep Inspection**: Raw socket-level analysis independent of the HTTP client
- **Certificate Pinning**: SHA-256 fingerprint verification per hostname via TLSInspector
- **Expiry Monitoring**: Automatic warnings when certificates expire within 30 days
- **Default TLS Verification**: TLS is verified by default; disabled only with explicit --no-verify
- **CA Bundle**: Uses certifi for trusted CA certificates

### File Integrity

- **SHA-256 Verification**: Incremental hashing during transfer via IntegrityVerifier
- **Secure Temp Files**: SecureTempFile context manager sets chmod 0o600 and auto-cleans on exit
- **Atomic Writes**: Temporary files are used during download; moved atomically on completion

### Network Security

- **Proxy Detection**: Reads HTTP_PROXY, HTTPS_PROXY, NO_PROXY environment variables
- **Custom Proxy Support**: Explicit --proxy flag for controlled routing
- **Retry Safety**: RetryClassifier distinguishes retryable from fatal errors

### Cookie & Credential Handling

- **In-memory only**: Cookies are never persisted to disk by Fluxion itself
- **Browser cookie extraction**: Requires explicit --browser-cookies flag (opt-in)
- **Stealth profiles**: Browser impersonation is explicit and user-controlled

## Known Security Considerations

- **--no-verify flag**: Disables TLS certificate verification entirely. Never use with sensitive data.
- **Browser cookie extraction** (--browser-cookies): Requires fluxion[stealth] and accesses your browser's local cookie store. Use with caution.
- **Plugin system**: Plugins run with full process privileges. Only install plugins from trusted sources.

## Responsible Disclosure

We follow responsible disclosure. After a fix is released, we will publicly acknowledge the reporter (if they wish) and publish a security advisory.
