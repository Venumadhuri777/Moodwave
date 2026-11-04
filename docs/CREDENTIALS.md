# External Credentials (Optional)

Moodwave is designed to function out-of-the-box without requiring mandatory API keys. The intent parsing engine contains an automated rule-based fallback, and the catalog uses local open metadata.

The user will provide these optional credentials in the final part of the hackathon if desired:

```env
# Optional: Google Gemini API Key for zero-shot natural language intent parsing.
# If omitted or empty, the backend automatically operates in rule-based fallback mode.
GEMINI_API_KEY=

# Optional: Jamendo Developer Client ID (only if needed to query live Jamendo track names or stream links).
JAMENDO_CLIENT_ID=
```

> **Note**: Do not fill in these values here or commit secrets to version control. The user will populate these in their local `.env` configuration during Phase 10.
