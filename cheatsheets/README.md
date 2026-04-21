# Toolkit

## `nmap`

### Scan ports 1-10000 with service/version detection, show only open ports

```bash
nmap -sV -p 1-10000 192.168.1.20
```

## `curl`

### Upload file

```bash
curl -s -X POST http://192.168.1.20:8000/upload \
  -F "file=@/tmp/document.txt"
```

## python

### Create a virtual environment

```bash
python3.12 -m venv venv
```

#### Activate the virtual environment

```bash
source venv/bin/activate
```

### Start a Python HTTP server serving a specific directory forever

```bash
python3 -m http.server 7777 --bind 0.0.0.0 --directory /tmp/webtest &
```

#### Search for the Python HTTP server process

```bash
ps -ef | grep '[p]ython3 -m http.server 7777'
```

#### Kill the Python HTTP server manually by PID

```bash
kill <PID>
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

## `psql`

### Connect to the PostgreSQL `postgres` database as `app_author`

```bash
psql -h 192.168.1.20 -U app_author -d postgres
```

### List all databases

```bash
postgres=> \l
```

### Connect to a specific database

```bash
postgres=> \c megacorp_internal
```

### List all tables in the current database/schema

```bash
megacorp_internal=> \dt
            List of tables
 Schema |   Name    | Type  |  Owner
--------+-----------+-------+----------
 public | api_keys  | table | postgres
 public | employees | table | postgres
(2 rows)
```

### Describe the structure of a table in the current database/schema

```bash
megacorp_internal=> \d employees
                 Table "public.employees"
 Column |  Type   | Nullable | Default
--------+---------+----------+---------
 id     | integer | not null |
 name   | text    |          |
 role   | text    |          |
 email  | text    |          |
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
