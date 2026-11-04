# Security & Privacy Policy: Moodwave

## 1. Data Classification & Boundaries

Moodwave enforces strict data boundary controls across the Android client, the FastAPI backend, and third-party LLM providers.

### 1.1 Stored Exclusively on the User's Device (Local Room Database)
- **Listening History**: Local record of past recommendations and queries.
- **Saved Tracks**: User's local bookmark collection.
- **Interaction History**: Local skip, save, and replay audit logs.
- **Offline Feedback Queue**: Unsent interaction events waiting for network reconnect.
*All local storage resides within the private Android application sandbox (`EncryptedSharedPreferences` / Room SQLite).*

### 1.2 Transmitted to the Moodwave Backend
- **Query Text**: The natural language prompt or selected mood chip label.
- **Anonymous User Identifier (`user_id`)**: A randomly generated client UUID (e.g., `anon_u_9021`). No personal identifiers (email, name, phone, device serial numbers, advertising IDs) are transmitted or stored.
- **Feedback Action Payloads**: Anonymous tuple `{ user_id, track_id, action }` strictly used for ephemeral in-session reranking.

### 1.3 Transmitted to External LLM Services (Google Gemini)
- **Prompt / Query Text Only**: Only the user's raw prompt string (e.g., *"upbeat music for cycling"*) is passed to the LLM prompt.
- **Zero Sensitive Context**: The `user_id`, IP address, device fingerprints, listening history, saved tracks, and session state are **never sent to the LLM**.

### 1.4 Third-Party Streaming Credentials
- **No Spotify or External Account Credentials**: Moodwave requires **no user login** and stores **no Spotify tokens, passwords, or authentication secrets**. The application is entirely self-contained and operates on open Jamendo metadata.

---

## 2. Threat Modeling & Mitigation Summary

| Threat / Risk | Mitigation Strategy |
| :--- | :--- |
| **User Profiling & Tracking** | All requests utilize ephemeral, randomly generated anonymous UUIDs. No PII is collected or persisted. |
| **Prompt Injection / Adversarial Input** | Strict JSON schema enforcement and validation on LLM output; deterministic regex fallback parser guards against injection; character length caps on input queries. |
| **Third-Party Data Harvesting** | User identifiers and historical telemetry are stripped prior to external LLM invocation. |
| **Credential Compromise** | No client credentials or third-party user tokens exist in the system. Optional server API keys reside solely in git-ignored `.env` configurations. |
