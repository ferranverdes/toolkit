# Toolkit

## `curl`

### Upload file

```bash
curl -s -X POST http://192.168.1.20:8000/upload \
  -F "file=@/tmp/document.txt"
```

## `ffuf`

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

## `aws`

### List available S3 buckets on custom endpoint

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
AWS_SECRET_ACCESS_KEY='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' \
aws --endpoint-url http://192.168.1.20:9000 s3 ls
```

### List all files inside `compliance-documents` bucket

```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE \
AWS_SECRET_ACCESS_KEY='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY' \
aws --endpoint-url http://192.168.1.20:9000 s3 ls s3://compliance-documents/ --recursive
```
