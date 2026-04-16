# Toolkit

## `curl`

### Upload file

```bash
curl -s -X POST http://192.168.1.20:8000/upload \
  -F "file=@/tmp/document.txt"
```

## Fuzzing

### GET endpoints, show all responses except 404

```bash
ffuf -u http://192.168.1.20:8000/FUZZ \
  -w toolkit/lists/ai_api_wordlist.txt \
  -mc all \
  -fc 404
```

### POST endpoints with empty JSON body, show all responses except 404/405

```bash
ffuf -u http://192.168.1.20:8000/FUZZ \
  -w toolkit/lists/ai_api_wordlist.txt \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{}' \
  -mc all \
  -fc 404,405
```
