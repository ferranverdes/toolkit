# Toolkit

## Reconnaissance

- [ ] Start with passive reconnaissance:
    - [ ] Search for public code repositories.
    - [ ] Use HTTP Header Fingerprinting to disclose implementation details.
- [ ] Conduct active reconnaissance using detection evasion techniques:
    - [ ] Proceed with AI service discovery through port scanning.
        - [ ] Inspect JavaScript files from web services.
    - [ ] Determine whether the API implements OpenAI-compatible endpoints.
    - [ ] Detect memory persistence across sessions.
- [ ] Test for Model Fingerprinting using:
    - [ ] Direct identity probing.
    - [ ] Contradiction testing.
    - [ ] Knowledge cutoff date.
    - [ ] Model-specific behaviour testing.
    - [ ] Capability boundary mapping.
    - [ ] Context window testing.
- [ ] Determine whether it provides RAG capabilities, such as source citations.
    - [ ] Detect citation consistency and source exposure.
    - [ ] Infer document retrieval behaviour.
    - [ ] Test for uploaded file processing.
- [ ] Determine if provides agent / tool capabilities.
    - [ ] Enumerate available tools through interaction.
    - [ ] Identify connectors (email, calendar, drive, CRM, search).

## Attacking AI Agents

- [ ] Test for direct prompt injection to bypass filters or system instructions.
    - [ ] Test single-turn jailbreak attempts.
    - [ ] Test context-building prompt injection by gradually establishing benign context across multiple turns until restricted behaviour is triggered.
    - [ ] Test role-play / persona hijacking techniques.
    - [ ] Test encoding / char-spacing / obfuscation-based bypasses.
- [ ] Test for indirect prompt injection via external content sources:
    - [ ] Cross-document fragmentation (split payload across multiple files or sources).
    - [ ] Hidden text in uploaded files or webpages (CSS / visual concealment bypass).
    - [ ] Code review agents through import resolution.
- [ ] Test agent memory attacks:
    - [ ] Database poisoning affecting future retrievals.
    - [ ] Predictable cross-session ID patterns.
