# Security Policy

## Supported Versions

| Version | Supported |
|:--------|:----------|
| 1.0.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability in Fluxion, **do not open a public issue**.

Instead, please report it responsibly:

1. **Email**: Send details to the maintainers via the repository's security advisory feature on GitHub
2. **GitHub Security Advisory**: Use the "Report a vulnerability" button under the Security tab

### What to Include

- Description of the vulnerability
- Steps to reproduce
- Potential impact assessment
- Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial assessment**: Within 7 days
- **Patch release**: As soon as a fix is verified

## Security Features

Fluxion includes built-in security capabilities:

- **TLS Deep Inspection** — Certificate chain validation, cipher suite analysis, expiry monitoring
- **Certificate Pinning** — SHA-256 fingerprint pinning per hostname
- **Integrity Verification** — SHA-256 checksum validation for all downloads
- **Secure Temp Files** — Restricted permissions (`0600`), automatic cleanup
- **No Shell Injection** — All external commands use parameterized execution
- **Proxy Transparency** — Explicit proxy detection and reporting

## Best Practices for Users

- Always use `--sha256` when downloading critical files
- Use `fluxion secure <url>` to inspect TLS before trusting endpoints
- Keep Fluxion updated to the latest version
- Review proxy settings with `fluxion doctor`
