# Toolkit

## Search public repos

```bash
grep -ri "password\|token\|secret\|api" .
```

```bash
git log -p | grep -i "password\|token\|secret\|api"
```

## Scan ports and services

```bash
IP="192.168.1.10"; nmap -sV -p- "$IP" -oA "$IP"
```

## Fingerprint services

### Check HTTP Headers

```bash
curl -I http://192.168.1.21
```

```bash
curl -i http://192.168.1.21
```

### Probe API endpoints

```bash
./scripts/api_probe.sh 192.168.1.10
```

### Inspect JavaScript assets

```bash
curl -s http://192.168.1.10 | grep -iE "hidden|data-endpoint=|data-url=|data-api="
```

```bash
curl -s http://192.168.1.10 | grep -iE "<script"
```

## Determine whether the API implements OpenAI-compatible endpoints

```bash
./scripts/extract_openapi_paths.py 192.168.1.10 ./lists/ai_api_wordlist.txt
```

## Conduct active recon

```bash
ffuf -u http://192.168.1.10:8000/FUZZ \
-w lists/ai_api_wordlist.txt \
-mc all \
-fc 404
```

```bash
ffuf -u http://192.168.1.10:8000/FUZZ \
-w lists/ai_api_wordlist.txt \
-X POST \
-H "Content-Type: application/json" \
-d '{}' \
-mc all \
-fc 404,405
```

### Test API versions

```bash
ffuf -u http://192.168.1.10:8000/V/FUZZ \
    -w lists/versions.txt:V \
    -w lists/ai_api_wordlist.txt:FUZZ \
    -mc all \
    -fc 404
```






        

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

## Attacking Multi-Agent Systems

```bash
./a2a_enum.sh 192.168.1.10
```

- [ ] Map all entry, processing, exit, and persistence points in the system.
    - [ ] Enumerate input vectors: user prompts, external files and URLs, API responses, inter-agent messages, webhooks.
        - [ ] Test prompt injection, document injection, and callback injection.
    - [ ] Enumerate processing vectors: prompt construction, tool selection, parameter building, state management, memory retrieval.
        - [ ] Test template injection, tool confusion, parameter injection, state manipulation, and memory poisoning.
    - [ ] Enumerate output vectors: agent responses, tool invocations, state modifications, external actions, handoffs between agents.
        - [ ] Test response injection, SSRF / SQL injection via tools, state corruption, unauthorized actions, and handoff hijacking.
    - [ ] Enumerate persistence vectors: shared memory, conversation history, configuration files, logs, caches.
        - [ ] Test memory persistence attacks, history injection, configuration backdoors, and cache poisoning.


