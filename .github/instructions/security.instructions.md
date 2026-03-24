# 🔒 Security & Secret Management Guardrails

## 🚫 Critical: Zero Secret Hardcoding

- **NEVER** generate strings that look like API Keys, Bearer Tokens, or Database Credentials (e.g., `sk-...`, `ghp_...`).
- If a secret is needed, **ALWAYS** use `os.getenv("VARIABLE_NAME")` or `pydantic-settings`.
- If a `.env` file is missing, the agent must first prompt the user to create one and add it to `.gitignore`.

## 📂 File System & Git Safety

- **ALWAYS** check for the existence of a `.gitignore` file before creating configuration files.
- **NEVER** suggest commands that involve `git add .` if sensitive files (like `.env` or `id_rsa`) are in the directory.

## 🧹 Data Sanitization

- Before logging "Observations" in the Reasoning Trace, **MUST** redact any sensitive strings (emails, tokens, or PII) found in tool outputs.
- Use a helper function `mask_sensitive_data(text: str)` for all external API responses.

## 🏗️ Secure Dependencies

- Only suggest well-maintained, standard libraries (e.g., `httpx` over `requests` for async, `pydantic` for validation).
- Avoid "experimental" or "unverified" third-party packages unless explicitly requested.
