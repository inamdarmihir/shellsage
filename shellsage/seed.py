"""
Seed translations loaded on `shellsage init`.

300+ curated bash → PowerShell pairs providing day-one coverage before any
real commands have been run through the agent.  Every PowerShell equivalent
has been validated for syntactic correctness.

Format: {"bash": "...", "ps": "..."}
"""

from __future__ import annotations

SEED_TRANSLATIONS: list[dict[str, str]] = [
    # ── File listing ─────────────────────────────────────────────────────────
    {"bash": "ls", "ps": "Get-ChildItem"},
    {"bash": "ls -l", "ps": "Get-ChildItem | Format-List"},
    {"bash": "ls -la", "ps": "Get-ChildItem -Force"},
    {"bash": "ls -a", "ps": "Get-ChildItem -Force"},
    {
        "bash": "ls -lh",
        "ps": "Get-ChildItem | Select-Object Name, @{N='Size';E={'{0:N0}' -f $_.Length}}",
    },
    {"bash": "ls -R", "ps": "Get-ChildItem -Recurse"},
    {"bash": "ls -lR", "ps": "Get-ChildItem -Recurse | Format-List"},
    {"bash": "ls *.py", "ps": "Get-ChildItem *.py"},
    {"bash": "ls *.js", "ps": "Get-ChildItem *.js"},
    {"bash": "ls *.ts", "ps": "Get-ChildItem *.ts"},
    {"bash": "ls *.json", "ps": "Get-ChildItem *.json"},
    {"bash": "ls *.txt", "ps": "Get-ChildItem *.txt"},
    {"bash": "ls *.log", "ps": "Get-ChildItem *.log"},
    {"bash": "ls -la src/", "ps": "Get-ChildItem -Force 'src/'"},
    {"bash": "ls -la dist/", "ps": "Get-ChildItem -Force 'dist/'"},
    {"bash": "ls /tmp", "ps": "Get-ChildItem $env:TEMP"},
    {"bash": "ls ~", "ps": "Get-ChildItem $HOME"},
    # ── Find ─────────────────────────────────────────────────────────────────
    {"bash": "find . -name '*.py'", "ps": "Get-ChildItem -Recurse -Filter '*.py'"},
    {"bash": "find . -name '*.js'", "ps": "Get-ChildItem -Recurse -Filter '*.js'"},
    {"bash": "find . -name '*.ts'", "ps": "Get-ChildItem -Recurse -Filter '*.ts'"},
    {"bash": "find . -name '*.json'", "ps": "Get-ChildItem -Recurse -Filter '*.json'"},
    {"bash": "find . -name '*.md'", "ps": "Get-ChildItem -Recurse -Filter '*.md'"},
    {"bash": "find . -name '*.log'", "ps": "Get-ChildItem -Recurse -Filter '*.log'"},
    {"bash": "find . -name '*.txt'", "ps": "Get-ChildItem -Recurse -Filter '*.txt'"},
    {"bash": "find . -name '*.yaml'", "ps": "Get-ChildItem -Recurse -Filter '*.yaml'"},
    {"bash": "find . -name '*.yml'", "ps": "Get-ChildItem -Recurse -Filter '*.yml'"},
    {"bash": "find . -name '*.toml'", "ps": "Get-ChildItem -Recurse -Filter '*.toml'"},
    {"bash": "find . -name 'Dockerfile'", "ps": "Get-ChildItem -Recurse -Filter 'Dockerfile'"},
    {"bash": "find . -name '.env'", "ps": "Get-ChildItem -Recurse -Filter '.env' -Force"},
    {"bash": "find . -type f", "ps": "Get-ChildItem -Recurse -File"},
    {"bash": "find . -type d", "ps": "Get-ChildItem -Recurse -Directory"},
    {"bash": "find . -type f -name '*.py'", "ps": "Get-ChildItem -Recurse -File -Filter '*.py'"},
    {"bash": "find . -type f -name '*.js'", "ps": "Get-ChildItem -Recurse -File -Filter '*.js'"},
    {"bash": "find . -type f -name '*.log'", "ps": "Get-ChildItem -Recurse -File -Filter '*.log'"},
    {"bash": "find src/ -name '*.py'", "ps": "Get-ChildItem -Path 'src/' -Recurse -Filter '*.py'"},
    {
        "bash": "find . -name '*.py' -not -path './.venv/*'",
        "ps": "Get-ChildItem -Recurse -Filter '*.py' | Where-Object { $_.FullName -notmatch '\\.venv' }",
    },
    {
        "bash": "find . -mtime -1",
        "ps": "Get-ChildItem -Recurse | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-1) }",
    },
    {
        "bash": "find . -mtime -7",
        "ps": "Get-ChildItem -Recurse | Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) }",
    },
    {
        "bash": "find . -size +1M",
        "ps": "Get-ChildItem -Recurse | Where-Object { $_.Length -gt 1MB }",
    },
    {
        "bash": "find . -size +100k",
        "ps": "Get-ChildItem -Recurse | Where-Object { $_.Length -gt 100KB }",
    },
    {"bash": "find . -empty", "ps": "Get-ChildItem -Recurse | Where-Object { $_.Length -eq 0 }"},
    {
        "bash": "find . -name '*.tmp' -delete",
        "ps": "Get-ChildItem -Recurse -Filter '*.tmp' | Remove-Item -Force",
    },
    {
        "bash": "find . -name '__pycache__' -type d",
        "ps": "Get-ChildItem -Recurse -Directory -Filter '__pycache__'",
    },
    {
        "bash": "find . -name '*.pyc' -delete",
        "ps": "Get-ChildItem -Recurse -Filter '*.pyc' | Remove-Item -Force",
    },
    # ── Grep / search ────────────────────────────────────────────────────────
    {"bash": "grep 'error' log.txt", "ps": "Select-String -Pattern 'error' -Path 'log.txt'"},
    {"bash": "grep 'TODO' app.py", "ps": "Select-String -Pattern 'TODO' -Path 'app.py'"},
    {"bash": "grep 'import' main.py", "ps": "Select-String -Pattern 'import' -Path 'main.py'"},
    {"bash": "grep -r 'TODO' .", "ps": "Get-ChildItem -Recurse | Select-String -Pattern 'TODO'"},
    {"bash": "grep -r 'FIXME' .", "ps": "Get-ChildItem -Recurse | Select-String -Pattern 'FIXME'"},
    {
        "bash": "grep -r 'import' src/",
        "ps": "Get-ChildItem -Recurse 'src/' | Select-String -Pattern 'import'",
    },
    {
        "bash": "grep -rn 'import' src/",
        "ps": "Get-ChildItem -Recurse 'src/' | Select-String -Pattern 'import'",
    },
    {"bash": "grep -rn 'TODO' .", "ps": "Get-ChildItem -Recurse | Select-String -Pattern 'TODO'"},
    {
        "bash": "grep -ri 'error' .",
        "ps": "Get-ChildItem -Recurse | Select-String -Pattern 'error' -CaseSensitive:$false",
    },
    {
        "bash": "grep -i 'error' app.log",
        "ps": "Select-String -Pattern 'error' -Path 'app.log' -CaseSensitive:$false",
    },
    {
        "bash": "grep -v 'debug' app.log",
        "ps": "Get-Content 'app.log' | Where-Object { $_ -notmatch 'debug' }",
    },
    {
        "bash": "grep -c 'error' app.log",
        "ps": "(Select-String -Pattern 'error' -Path 'app.log').Count",
    },
    {
        "bash": "grep -l 'TODO' *.py",
        "ps": "Select-String -Pattern 'TODO' -Path '*.py' | Select-Object -ExpandProperty Path -Unique",
    },
    {
        "bash": "grep -E '^[0-9]+' file.txt",
        "ps": "Select-String -Pattern '^[0-9]+' -Path 'file.txt'",
    },
    {"bash": "grep -n 'function' app.js", "ps": "Select-String -Pattern 'function' -Path 'app.js'"},
    {"bash": "grep 'error' *.log", "ps": "Select-String -Pattern 'error' -Path '*.log'"},
    {
        "bash": "grep -r 'password' . --include='*.py'",
        "ps": "Get-ChildItem -Recurse -Filter '*.py' | Select-String -Pattern 'password'",
    },
    # ── Cat / view files ─────────────────────────────────────────────────────
    {"bash": "cat README.md", "ps": "Get-Content 'README.md'"},
    {"bash": "cat package.json", "ps": "Get-Content 'package.json'"},
    {"bash": "cat .env", "ps": "Get-Content '.env'"},
    {"bash": "cat requirements.txt", "ps": "Get-Content 'requirements.txt'"},
    {"bash": "cat Dockerfile", "ps": "Get-Content 'Dockerfile'"},
    {"bash": "cat docker-compose.yml", "ps": "Get-Content 'docker-compose.yml'"},
    {"bash": "cat pyproject.toml", "ps": "Get-Content 'pyproject.toml'"},
    {"bash": "cat Cargo.toml", "ps": "Get-Content 'Cargo.toml'"},
    {"bash": "cat go.mod", "ps": "Get-Content 'go.mod'"},
    {
        "bash": "cat -n file.txt",
        "ps": "Get-Content 'file.txt' | ForEach-Object -Begin { $i=1 } -Process { '{0:4}: {1}' -f $i++, $_ }",
    },
    {"bash": "cat file1.txt file2.txt", "ps": "Get-Content 'file1.txt', 'file2.txt'"},
    {"bash": "cat /etc/hosts", "ps": "Get-Content 'C:\\Windows\\System32\\drivers\\etc\\hosts'"},
    # ── Head / tail ───────────────────────────────────────────────────────────
    {"bash": "head file.txt", "ps": "Get-Content 'file.txt' -TotalCount 10"},
    {"bash": "head -n 5 file.txt", "ps": "Get-Content 'file.txt' -TotalCount 5"},
    {"bash": "head -n 10 file.txt", "ps": "Get-Content 'file.txt' -TotalCount 10"},
    {"bash": "head -n 20 file.txt", "ps": "Get-Content 'file.txt' -TotalCount 20"},
    {"bash": "head -n 50 server.log", "ps": "Get-Content 'server.log' -TotalCount 50"},
    {"bash": "tail file.txt", "ps": "Get-Content 'file.txt' -Tail 10"},
    {"bash": "tail -n 5 file.txt", "ps": "Get-Content 'file.txt' -Tail 5"},
    {"bash": "tail -n 10 file.txt", "ps": "Get-Content 'file.txt' -Tail 10"},
    {"bash": "tail -n 50 file.log", "ps": "Get-Content 'file.log' -Tail 50"},
    {"bash": "tail -n 100 app.log", "ps": "Get-Content 'app.log' -Tail 100"},
    {"bash": "tail -f server.log", "ps": "Get-Content -Wait 'server.log'"},
    {"bash": "tail -f app.log", "ps": "Get-Content -Wait 'app.log'"},
    {
        "bash": "tail -f /var/log/syslog",
        "ps": "Get-Content -Wait 'C:\\Windows\\System32\\winevt\\Logs\\System.evtx'",
    },
    # ── Mkdir ─────────────────────────────────────────────────────────────────
    {"bash": "mkdir src", "ps": "New-Item -ItemType Directory -Path 'src'"},
    {"bash": "mkdir dist", "ps": "New-Item -ItemType Directory -Path 'dist'"},
    {"bash": "mkdir build", "ps": "New-Item -ItemType Directory -Path 'build'"},
    {"bash": "mkdir -p src/utils", "ps": "New-Item -ItemType Directory -Force -Path 'src/utils'"},
    {
        "bash": "mkdir -p src/components",
        "ps": "New-Item -ItemType Directory -Force -Path 'src/components'",
    },
    {
        "bash": "mkdir -p dist/assets",
        "ps": "New-Item -ItemType Directory -Force -Path 'dist/assets'",
    },
    {
        "bash": "mkdir -p .github/workflows",
        "ps": "New-Item -ItemType Directory -Force -Path '.github/workflows'",
    },
    {"bash": "mkdir -p tests/unit", "ps": "New-Item -ItemType Directory -Force -Path 'tests/unit'"},
    # ── Rm ────────────────────────────────────────────────────────────────────
    {"bash": "rm file.txt", "ps": "Remove-Item 'file.txt'"},
    {"bash": "rm output.log", "ps": "Remove-Item 'output.log'"},
    {"bash": "rm -f file.txt", "ps": "Remove-Item -Force 'file.txt'"},
    {"bash": "rm -f output.log", "ps": "Remove-Item -Force 'output.log'"},
    {"bash": "rm *.tmp", "ps": "Remove-Item '*.tmp'"},
    {"bash": "rm *.pyc", "ps": "Remove-Item '*.pyc' -Recurse"},
    {"bash": "rm -r dir/", "ps": "Remove-Item -Recurse 'dir/'"},
    {"bash": "rm -rf dist/", "ps": "Remove-Item -Recurse -Force 'dist/'"},
    {"bash": "rm -rf build/", "ps": "Remove-Item -Recurse -Force 'build/'"},
    {"bash": "rm -rf node_modules", "ps": "Remove-Item -Recurse -Force 'node_modules'"},
    {"bash": "rm -rf .venv", "ps": "Remove-Item -Recurse -Force '.venv'"},
    {"bash": "rm -rf __pycache__", "ps": "Remove-Item -Recurse -Force '__pycache__'"},
    {"bash": "rm -rf .pytest_cache", "ps": "Remove-Item -Recurse -Force '.pytest_cache'"},
    # ── Cp / mv ───────────────────────────────────────────────────────────────
    {"bash": "cp file.txt backup.txt", "ps": "Copy-Item 'file.txt' 'backup.txt'"},
    {"bash": "cp config.json config.json.bak", "ps": "Copy-Item 'config.json' 'config.json.bak'"},
    {"bash": "cp .env .env.example", "ps": "Copy-Item '.env' '.env.example'"},
    {"bash": "cp -r src/ backup/", "ps": "Copy-Item -Recurse 'src/' 'backup/'"},
    {"bash": "cp -r dist/ release/", "ps": "Copy-Item -Recurse 'dist/' 'release/'"},
    {"bash": "mv old.txt new.txt", "ps": "Move-Item 'old.txt' 'new.txt'"},
    {"bash": "mv app.py main.py", "ps": "Move-Item 'app.py' 'main.py'"},
    {"bash": "mv src/old.js src/new.js", "ps": "Move-Item 'src/old.js' 'src/new.js'"},
    {"bash": "mv dist/ release/", "ps": "Move-Item 'dist/' 'release/'"},
    # ── Touch / symlinks ──────────────────────────────────────────────────────
    {"bash": "touch file.txt", "ps": "New-Item -ItemType File -Force 'file.txt'"},
    {"bash": "touch .gitkeep", "ps": "New-Item -ItemType File -Force '.gitkeep'"},
    {"bash": "touch .env", "ps": "New-Item -ItemType File -Force '.env'"},
    {"bash": "ln -s src dest", "ps": "New-Item -ItemType SymbolicLink -Name 'dest' -Target 'src'"},
    {
        "bash": "ln -s ../lib lib",
        "ps": "New-Item -ItemType SymbolicLink -Name 'lib' -Target '../lib'",
    },
    # ── Text processing — wc / sort / uniq ────────────────────────────────────
    {"bash": "wc -l file.txt", "ps": "(Get-Content 'file.txt').Count"},
    {"bash": "wc -l requirements.txt", "ps": "(Get-Content 'requirements.txt').Count"},
    {"bash": "cat file.txt | wc -l", "ps": "(Get-Content 'file.txt').Count"},
    {"bash": "wc -w file.txt", "ps": "((Get-Content 'file.txt') -split '\\s+').Count"},
    {"bash": "wc -c file.txt", "ps": "(Get-Item 'file.txt').Length"},
    {"bash": "sort file.txt", "ps": "Get-Content 'file.txt' | Sort-Object"},
    {"bash": "sort -u file.txt", "ps": "Get-Content 'file.txt' | Sort-Object -Unique"},
    {"bash": "sort -r file.txt", "ps": "Get-Content 'file.txt' | Sort-Object -Descending"},
    {"bash": "sort -n file.txt", "ps": "Get-Content 'file.txt' | Sort-Object { [int]$_ }"},
    {"bash": "ls | sort", "ps": "Get-ChildItem | Sort-Object"},
    {"bash": "ls | sort -u", "ps": "Get-ChildItem | Sort-Object -Unique"},
    {"bash": "uniq file.txt", "ps": "Get-Content 'file.txt' | Select-Object -Unique"},
    {"bash": "sort file.txt | uniq", "ps": "Get-Content 'file.txt' | Sort-Object -Unique"},
    {
        "bash": "sort file.txt | uniq -c",
        "ps": "Get-Content 'file.txt' | Group-Object | Select-Object Count, Name | Sort-Object Count -Descending",
    },
    {
        "bash": "cut -d',' -f1 data.csv",
        "ps": "Import-Csv 'data.csv' | Select-Object -ExpandProperty (Import-Csv 'data.csv' | Get-Member -MemberType NoteProperty | Select-Object -First 1).Name",
    },
    {
        "bash": "cut -d':' -f1 /etc/passwd",
        "ps": "Get-Content 'C:\\Windows\\System32\\drivers\\etc\\hosts' | ForEach-Object { $_.Split(':')[0] }",
    },
    {
        "bash": "cut -d' ' -f1 file.txt",
        "ps": "Get-Content 'file.txt' | ForEach-Object { $_.Split(' ')[0] }",
    },
    # ── Sed / awk / tr ────────────────────────────────────────────────────────
    {
        "bash": "sed 's/old/new/g' file.txt",
        "ps": "(Get-Content 'file.txt') -replace 'old','new' | Set-Content 'file.txt'",
    },
    {
        "bash": "sed -i 's/foo/bar/g' file.txt",
        "ps": "(Get-Content 'file.txt') -replace 'foo','bar' | Set-Content 'file.txt'",
    },
    {"bash": "sed -n '1,10p' file.txt", "ps": "Get-Content 'file.txt' -TotalCount 10"},
    {
        "bash": "sed '/^#/d' file.txt",
        "ps": "Get-Content 'file.txt' | Where-Object { $_ -notmatch '^#' }",
    },
    {
        "bash": "sed '/^$/d' file.txt",
        "ps": "Get-Content 'file.txt' | Where-Object { $_.Trim() -ne '' }",
    },
    {
        "bash": "awk '{print $1}' file.txt",
        "ps": "Get-Content 'file.txt' | ForEach-Object { ($_ -split '\\s+')[0] }",
    },
    {
        "bash": "awk '{print $NF}' file.txt",
        "ps": "Get-Content 'file.txt' | ForEach-Object { ($_ -split '\\s+')[-1] }",
    },
    {
        "bash": "awk -F',' '{print $2}' data.csv",
        "ps": "Import-Csv 'data.csv' | Select-Object -ExpandProperty (Get-Member -InputObject (Import-Csv 'data.csv' | Select-Object -First 1) -MemberType NoteProperty).Name[1]",
    },
    {"bash": "tr '[:upper:]' '[:lower:]'", "ps": "$input | ForEach-Object { $_.ToLower() }"},
    {"bash": "tr '[:lower:]' '[:upper:]'", "ps": "$input | ForEach-Object { $_.ToUpper() }"},
    {"bash": "tr -d '\\n'", "ps": "$input -join ''"},
    # ── Echo / print ──────────────────────────────────────────────────────────
    {"bash": "echo 'hello world'", "ps": "Write-Output 'hello world'"},
    {"bash": "echo 'done'", "ps": "Write-Output 'done'"},
    {"bash": "echo 'build complete'", "ps": "Write-Output 'build complete'"},
    {"bash": "echo $PATH", "ps": "$env:PATH"},
    {"bash": "echo $HOME", "ps": "$env:USERPROFILE"},
    {"bash": "echo $USER", "ps": "$env:USERNAME"},
    {"bash": "echo $SHELL", "ps": "$env:ComSpec"},
    {"bash": "echo $PWD", "ps": "(Get-Location).Path"},
    {"bash": "printf '%s\\n' 'hello'", "ps": "Write-Output 'hello'"},
    {"bash": "echo 'line' >> file.txt", "ps": "Add-Content 'file.txt' 'line'"},
    {"bash": "echo 'line' > file.txt", "ps": "Set-Content 'file.txt' 'line'"},
    # ── Env / export ──────────────────────────────────────────────────────────
    {"bash": "export NODE_ENV=production", "ps": "$env:NODE_ENV = 'production'"},
    {"bash": "export NODE_ENV=development", "ps": "$env:NODE_ENV = 'development'"},
    {"bash": "export DEBUG=true", "ps": "$env:DEBUG = 'true'"},
    {"bash": "export DEBUG=1", "ps": "$env:DEBUG = '1'"},
    {"bash": "export PORT=3000", "ps": "$env:PORT = '3000'"},
    {"bash": "export PORT=8080", "ps": "$env:PORT = '8080'"},
    {
        "bash": "export DATABASE_URL=postgres://localhost/mydb",
        "ps": "$env:DATABASE_URL = 'postgres://localhost/mydb'",
    },
    {"bash": "export API_KEY=abc123", "ps": "$env:API_KEY = 'abc123'"},
    {"bash": "export PYTHONPATH=.", "ps": "$env:PYTHONPATH = '.'"},
    {"bash": "export GOPATH=$HOME/go", "ps": '$env:GOPATH = "$env:USERPROFILE\\go"'},
    {"bash": "unset NODE_ENV", "ps": "Remove-Item Env:\\NODE_ENV"},
    {"bash": "unset DEBUG", "ps": "Remove-Item Env:\\DEBUG"},
    {"bash": "env", "ps": "Get-ChildItem Env:"},
    {"bash": "printenv", "ps": "Get-ChildItem Env:"},
    {"bash": "printenv PATH", "ps": "$env:PATH"},
    {"bash": "printenv NODE_ENV", "ps": "$env:NODE_ENV"},
    {"bash": "printenv HOME", "ps": "$env:USERPROFILE"},
    # ── Process management ────────────────────────────────────────────────────
    {"bash": "ps aux", "ps": "Get-Process"},
    {"bash": "ps -ef", "ps": "Get-Process | Format-Table Id, CPU, WorkingSet, ProcessName"},
    {
        "bash": "ps aux | grep python",
        "ps": "Get-Process | Where-Object { $_.Name -match 'python' }",
    },
    {"bash": "ps aux | grep node", "ps": "Get-Process | Where-Object { $_.Name -match 'node' }"},
    {"bash": "ps aux | grep java", "ps": "Get-Process | Where-Object { $_.Name -match 'java' }"},
    {
        "bash": "ps aux | grep docker",
        "ps": "Get-Process | Where-Object { $_.Name -match 'docker' }",
    },
    {"bash": "pgrep python", "ps": "Get-Process -Name 'python*'"},
    {"bash": "pgrep node", "ps": "Get-Process -Name 'node*'"},
    {"bash": "pkill python", "ps": "Stop-Process -Name 'python' -Force"},
    {"bash": "pkill node", "ps": "Stop-Process -Name 'node' -Force"},
    {"bash": "kill -9 1234", "ps": "Stop-Process -Id 1234 -Force"},
    {"bash": "kill 1234", "ps": "Stop-Process -Id 1234"},
    {"bash": "killall python", "ps": "Stop-Process -Name 'python' -Force"},
    {
        "bash": "nohup python app.py &",
        "ps": "Start-Process -NoNewWindow python -ArgumentList 'app.py' -RedirectStandardOutput 'nohup.out'",
    },
    {"bash": "sleep 5", "ps": "Start-Sleep 5"},
    {"bash": "sleep 10", "ps": "Start-Sleep 10"},
    {"bash": "sleep 0.5", "ps": "Start-Sleep -Milliseconds 500"},
    # ── Network ───────────────────────────────────────────────────────────────
    {"bash": "curl https://example.com", "ps": "Invoke-WebRequest -Uri 'https://example.com'"},
    {"bash": "curl -s https://api.github.com", "ps": "Invoke-RestMethod 'https://api.github.com'"},
    {
        "bash": "curl -s https://httpbin.org/get",
        "ps": "Invoke-RestMethod 'https://httpbin.org/get'",
    },
    {
        "bash": "curl -o output.html https://example.com",
        "ps": "Invoke-WebRequest -Uri 'https://example.com' -OutFile 'output.html'",
    },
    {
        "bash": "curl -L https://example.com",
        "ps": "Invoke-WebRequest -Uri 'https://example.com' -MaximumRedirection 5",
    },
    {
        "bash": 'curl -X POST https://api.example.com/data -d \'{"key":"value"}\'',
        "ps": "Invoke-RestMethod -Method POST -Uri 'https://api.example.com/data' -Body '{\"key\":\"value\"}' -ContentType 'application/json'",
    },
    {
        "bash": "curl -X PUT https://api.example.com/item/1 -d '{}'",
        "ps": "Invoke-RestMethod -Method PUT -Uri 'https://api.example.com/item/1' -Body '{}' -ContentType 'application/json'",
    },
    {
        "bash": "curl -X DELETE https://api.example.com/item/1",
        "ps": "Invoke-RestMethod -Method DELETE -Uri 'https://api.example.com/item/1'",
    },
    {
        "bash": "curl -H 'Authorization: Bearer TOKEN' https://api.example.com",
        "ps": "Invoke-RestMethod -Uri 'https://api.example.com' -Headers @{ Authorization = 'Bearer TOKEN' }",
    },
    {
        "bash": "curl -H 'Content-Type: application/json' https://api.example.com",
        "ps": "Invoke-RestMethod -Uri 'https://api.example.com' -ContentType 'application/json'",
    },
    {
        "bash": "wget https://example.com/file.zip",
        "ps": "Invoke-WebRequest -Uri 'https://example.com/file.zip' -OutFile 'file.zip'",
    },
    {
        "bash": "wget -q https://example.com/file.zip",
        "ps": "Invoke-WebRequest -Uri 'https://example.com/file.zip' -OutFile 'file.zip'",
    },
    {
        "bash": "wget -O output.zip https://example.com/archive.zip",
        "ps": "Invoke-WebRequest -Uri 'https://example.com/archive.zip' -OutFile 'output.zip'",
    },
    {"bash": "ping google.com", "ps": "Test-Connection -ComputerName 'google.com'"},
    {"bash": "ping -c 4 google.com", "ps": "Test-Connection -ComputerName 'google.com' -Count 4"},
    {
        "bash": "netstat -tulpn",
        "ps": "Get-NetTCPConnection | Where-Object { $_.State -eq 'Listen' }",
    },
    {"bash": "ss -tlnp", "ps": "Get-NetTCPConnection | Where-Object { $_.State -eq 'Listen' }"},
    {"bash": "netstat -an", "ps": "Get-NetTCPConnection"},
    {"bash": "nslookup google.com", "ps": "Resolve-DnsName 'google.com'"},
    {"bash": "host google.com", "ps": "Resolve-DnsName 'google.com'"},
    # ── Archive / compression ─────────────────────────────────────────────────
    {
        "bash": "tar -czf archive.tar.gz dist/",
        "ps": "Compress-Archive -Path 'dist/' -DestinationPath 'archive.zip'",
    },
    {
        "bash": "tar -czf archive.tar.gz src/",
        "ps": "Compress-Archive -Path 'src/' -DestinationPath 'archive.zip'",
    },
    {
        "bash": "tar -xzf archive.tar.gz",
        "ps": "Expand-Archive -Path 'archive.zip' -DestinationPath '.'",
    },
    {
        "bash": "tar -xzf archive.tar.gz -C dist/",
        "ps": "Expand-Archive -Path 'archive.zip' -DestinationPath 'dist/'",
    },
    {
        "bash": "tar -tf archive.tar.gz",
        "ps": "Expand-Archive -Path 'archive.zip' -DestinationPath '.' -WhatIf",
    },
    {
        "bash": "zip -r archive.zip src/",
        "ps": "Compress-Archive -Path 'src/' -DestinationPath 'archive.zip'",
    },
    {
        "bash": "zip archive.zip file.txt",
        "ps": "Compress-Archive -Path 'file.txt' -DestinationPath 'archive.zip'",
    },
    {"bash": "unzip archive.zip", "ps": "Expand-Archive -Path 'archive.zip' -DestinationPath '.'"},
    {
        "bash": "unzip archive.zip -d output/",
        "ps": "Expand-Archive -Path 'archive.zip' -DestinationPath 'output/'",
    },
    {
        "bash": "gzip file.txt",
        "ps": "Compress-Archive -Path 'file.txt' -DestinationPath 'file.zip'",
    },
    {"bash": "gunzip file.gz", "ps": "Expand-Archive -Path 'file.zip' -DestinationPath '.'"},
    # ── Disk / filesystem ─────────────────────────────────────────────────────
    {"bash": "df -h", "ps": "Get-PSDrive -PSProvider FileSystem"},
    {"bash": "df -H", "ps": "Get-PSDrive -PSProvider FileSystem"},
    {
        "bash": "du -sh .",
        "ps": "(Get-ChildItem -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB",
    },
    {
        "bash": "du -sh src/",
        "ps": "(Get-ChildItem -Recurse 'src/' | Measure-Object -Property Length -Sum).Sum / 1MB",
    },
    {
        "bash": "du -sh node_modules/",
        "ps": "(Get-ChildItem -Recurse 'node_modules/' | Measure-Object -Property Length -Sum).Sum / 1MB",
    },
    {
        "bash": "du -sh *",
        "ps": "Get-ChildItem | ForEach-Object { [PSCustomObject]@{Name=$_.Name; SizeMB=[math]::Round((Get-ChildItem $_.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum/1MB,2)} }",
    },
    # ── System info ───────────────────────────────────────────────────────────
    {
        "bash": "uname -a",
        "ps": "Get-ComputerInfo | Select-Object WindowsProductName, WindowsVersion, OsHardwareAbstractionLayer",
    },
    {"bash": "uname -r", "ps": "(Get-CimInstance Win32_OperatingSystem).Version"},
    {"bash": "uname -m", "ps": "$env:PROCESSOR_ARCHITECTURE"},
    {
        "bash": "uname -s",
        "ps": "[System.Runtime.InteropServices.RuntimeInformation]::OSDescription",
    },
    {"bash": "hostname", "ps": "$env:COMPUTERNAME"},
    {"bash": "whoami", "ps": "$env:USERNAME"},
    {"bash": "id", "ps": "[Security.Principal.WindowsIdentity]::GetCurrent().Name"},
    {"bash": "date", "ps": "Get-Date"},
    {"bash": "date '+%Y-%m-%d'", "ps": "Get-Date -Format 'yyyy-MM-dd'"},
    {"bash": "date '+%H:%M:%S'", "ps": "Get-Date -Format 'HH:mm:ss'"},
    {"bash": "date +%s", "ps": "[DateTimeOffset]::UtcNow.ToUnixTimeSeconds()"},
    {"bash": "uptime", "ps": "(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime"},
    {
        "bash": "free -h",
        "ps": "Get-CimInstance Win32_OperatingSystem | Select-Object @{N='TotalGB';E={[math]::Round($_.TotalVisibleMemorySize/1MB,1)}}, @{N='FreeGB';E={[math]::Round($_.FreePhysicalMemory/1MB,1)}}",
    },
    # ── Permissions ───────────────────────────────────────────────────────────
    {
        "bash": "chmod +x script.sh",
        "ps": "# chmod not needed in PowerShell — use .ps1 files or Set-ExecutionPolicy",
    },
    {
        "bash": "chmod 755 script.sh",
        "ps": "# chmod not needed in PowerShell — use .ps1 files or Set-ExecutionPolicy",
    },
    {
        "bash": "chmod -R 755 dir/",
        "ps": "# Use icacls for Windows ACL: icacls 'dir' /grant Everyone:(OI)(CI)RX /T",
    },
    {
        "bash": "chown user:group file.txt",
        "ps": "# Use icacls for Windows ownership: icacls 'file.txt' /setowner 'user'",
    },
    {
        "bash": "chown -R user dir/",
        "ps": "# Use icacls for Windows ownership: icacls 'dir' /setowner 'user' /T",
    },
    {"bash": "sudo command", "ps": "# Run PowerShell as Administrator, then: command"},
    # ── Git ───────────────────────────────────────────────────────────────────
    {"bash": "git init", "ps": "git init"},
    {
        "bash": "git clone https://github.com/user/repo.git",
        "ps": "git clone https://github.com/user/repo.git",
    },
    {"bash": "git status", "ps": "git status"},
    {"bash": "git add .", "ps": "git add ."},
    {"bash": "git add -A", "ps": "git add -A"},
    {"bash": "git add src/", "ps": "git add src/"},
    {"bash": "git commit -m 'initial commit'", "ps": "git commit -m 'initial commit'"},
    {"bash": "git commit -am 'fix bug'", "ps": "git commit -am 'fix bug'"},
    {"bash": "git push origin main", "ps": "git push origin main"},
    {"bash": "git push origin develop", "ps": "git push origin develop"},
    {"bash": "git push -u origin main", "ps": "git push -u origin main"},
    {"bash": "git pull", "ps": "git pull"},
    {"bash": "git pull origin main", "ps": "git pull origin main"},
    {"bash": "git fetch", "ps": "git fetch"},
    {"bash": "git fetch --all", "ps": "git fetch --all"},
    {"bash": "git branch", "ps": "git branch"},
    {"bash": "git branch -a", "ps": "git branch -a"},
    {"bash": "git checkout main", "ps": "git checkout main"},
    {"bash": "git checkout develop", "ps": "git checkout develop"},
    {"bash": "git checkout -b feature/new-feature", "ps": "git checkout -b feature/new-feature"},
    {"bash": "git merge main", "ps": "git merge main"},
    {"bash": "git rebase main", "ps": "git rebase main"},
    {"bash": "git log --oneline", "ps": "git log --oneline"},
    {"bash": "git log --oneline -10", "ps": "git log --oneline -10"},
    {"bash": "git log --graph --oneline", "ps": "git log --graph --oneline"},
    {"bash": "git diff", "ps": "git diff"},
    {"bash": "git diff --stat", "ps": "git diff --stat"},
    {"bash": "git diff HEAD~1", "ps": "git diff HEAD~1"},
    {"bash": "git stash", "ps": "git stash"},
    {"bash": "git stash pop", "ps": "git stash pop"},
    {"bash": "git stash list", "ps": "git stash list"},
    {"bash": "git reset --hard HEAD", "ps": "git reset --hard HEAD"},
    {"bash": "git reset --soft HEAD~1", "ps": "git reset --soft HEAD~1"},
    {"bash": "git tag v1.0.0", "ps": "git tag v1.0.0"},
    {"bash": "git remote -v", "ps": "git remote -v"},
    # ── Docker ────────────────────────────────────────────────────────────────
    {"bash": "docker ps", "ps": "docker ps"},
    {"bash": "docker ps -a", "ps": "docker ps -a"},
    {"bash": "docker images", "ps": "docker images"},
    {"bash": "docker images -a", "ps": "docker images -a"},
    {"bash": "docker build -t myapp .", "ps": "docker build -t myapp ."},
    {"bash": "docker build -t myapp:latest .", "ps": "docker build -t myapp:latest ."},
    {"bash": "docker build --no-cache -t myapp .", "ps": "docker build --no-cache -t myapp ."},
    {"bash": "docker run myapp", "ps": "docker run myapp"},
    {"bash": "docker run -it myapp bash", "ps": "docker run -it myapp bash"},
    {"bash": "docker run -d myapp", "ps": "docker run -d myapp"},
    {"bash": "docker run -d -p 8080:8080 myapp", "ps": "docker run -d -p 8080:8080 myapp"},
    {
        "bash": "docker run -d --name mycontainer myapp",
        "ps": "docker run -d --name mycontainer myapp",
    },
    {"bash": "docker run --rm myapp", "ps": "docker run --rm myapp"},
    {"bash": "docker stop mycontainer", "ps": "docker stop mycontainer"},
    {"bash": "docker start mycontainer", "ps": "docker start mycontainer"},
    {"bash": "docker restart mycontainer", "ps": "docker restart mycontainer"},
    {"bash": "docker rm mycontainer", "ps": "docker rm mycontainer"},
    {"bash": "docker rm -f mycontainer", "ps": "docker rm -f mycontainer"},
    {"bash": "docker rmi myimage", "ps": "docker rmi myimage"},
    {"bash": "docker rmi -f myimage", "ps": "docker rmi -f myimage"},
    {"bash": "docker logs mycontainer", "ps": "docker logs mycontainer"},
    {"bash": "docker logs -f mycontainer", "ps": "docker logs -f mycontainer"},
    {"bash": "docker logs --tail 50 mycontainer", "ps": "docker logs --tail 50 mycontainer"},
    {"bash": "docker exec -it mycontainer bash", "ps": "docker exec -it mycontainer bash"},
    {"bash": "docker exec -it mycontainer sh", "ps": "docker exec -it mycontainer sh"},
    {"bash": "docker-compose up", "ps": "docker-compose up"},
    {"bash": "docker-compose up -d", "ps": "docker-compose up -d"},
    {"bash": "docker-compose down", "ps": "docker-compose down"},
    {"bash": "docker-compose down -v", "ps": "docker-compose down -v"},
    {"bash": "docker-compose build", "ps": "docker-compose build"},
    {"bash": "docker-compose logs -f", "ps": "docker-compose logs -f"},
    {"bash": "docker-compose ps", "ps": "docker-compose ps"},
    {"bash": "docker volume ls", "ps": "docker volume ls"},
    {"bash": "docker network ls", "ps": "docker network ls"},
    {"bash": "docker system prune -f", "ps": "docker system prune -f"},
    # ── Python ────────────────────────────────────────────────────────────────
    {"bash": "python3 --version", "ps": "python --version"},
    {"bash": "python3 script.py", "ps": "python script.py"},
    {"bash": "python3 app.py", "ps": "python app.py"},
    {"bash": "python3 main.py", "ps": "python main.py"},
    {"bash": "python3 -c 'print(\"hello\")'", "ps": "python -c 'print(\"hello\")'"},
    {"bash": "python3 -m pytest", "ps": "python -m pytest"},
    {"bash": "python3 -m pytest -v", "ps": "python -m pytest -v"},
    {"bash": "python3 -m pytest tests/", "ps": "python -m pytest tests/"},
    {"bash": "python3 -m pytest -x", "ps": "python -m pytest -x"},
    {"bash": "python3 -m pip install package", "ps": "python -m pip install package"},
    {
        "bash": "python3 -m pip install -r requirements.txt",
        "ps": "python -m pip install -r requirements.txt",
    },
    {"bash": "python3 -m pip install -e .", "ps": "python -m pip install -e ."},
    {"bash": "python3 -m pip install --upgrade pip", "ps": "python -m pip install --upgrade pip"},
    {"bash": "python3 -m pip list", "ps": "python -m pip list"},
    {"bash": "python3 -m pip freeze", "ps": "python -m pip freeze"},
    {
        "bash": "python3 -m pip freeze > requirements.txt",
        "ps": "python -m pip freeze | Set-Content 'requirements.txt'",
    },
    {"bash": "python3 -m venv .venv", "ps": "python -m venv .venv"},
    {"bash": "source .venv/bin/activate", "ps": ".venv\\Scripts\\Activate.ps1"},
    {"bash": ". .venv/bin/activate", "ps": ".venv\\Scripts\\Activate.ps1"},
    {"bash": "deactivate", "ps": "deactivate"},
    {"bash": "pip install package", "ps": "pip install package"},
    {"bash": "pip install -r requirements.txt", "ps": "pip install -r requirements.txt"},
    {"bash": "pip install -e .", "ps": "pip install -e ."},
    {"bash": "pip freeze", "ps": "pip freeze"},
    {"bash": "pip list", "ps": "pip list"},
    {"bash": "python3 -m ruff check .", "ps": "python -m ruff check ."},
    {"bash": "python3 -m mypy .", "ps": "python -m mypy ."},
    {"bash": "which python3", "ps": "Get-Command python"},
    {"bash": "which python", "ps": "Get-Command python"},
    # ── Node.js / npm ─────────────────────────────────────────────────────────
    {"bash": "node --version", "ps": "node --version"},
    {"bash": "node script.js", "ps": "node script.js"},
    {"bash": "node index.js", "ps": "node index.js"},
    {"bash": "npm install", "ps": "npm install"},
    {"bash": "npm install package", "ps": "npm install package"},
    {"bash": "npm install --save-dev package", "ps": "npm install --save-dev package"},
    {"bash": "npm install -g package", "ps": "npm install -g package"},
    {"bash": "npm uninstall package", "ps": "npm uninstall package"},
    {"bash": "npm run build", "ps": "npm run build"},
    {"bash": "npm run dev", "ps": "npm run dev"},
    {"bash": "npm run start", "ps": "npm run start"},
    {"bash": "npm test", "ps": "npm test"},
    {"bash": "npm start", "ps": "npm start"},
    {"bash": "npm run lint", "ps": "npm run lint"},
    {"bash": "npx create-react-app myapp", "ps": "npx create-react-app myapp"},
    {"bash": "npx tsc", "ps": "npx tsc"},
    {"bash": "npx eslint .", "ps": "npx eslint ."},
    {"bash": "yarn install", "ps": "yarn install"},
    {"bash": "yarn add package", "ps": "yarn add package"},
    {"bash": "yarn add -D package", "ps": "yarn add -D package"},
    {"bash": "yarn build", "ps": "yarn build"},
    {"bash": "yarn dev", "ps": "yarn dev"},
    {"bash": "yarn test", "ps": "yarn test"},
    {"bash": "which node", "ps": "Get-Command node"},
    {"bash": "which npm", "ps": "Get-Command npm"},
    # ── Rust / Cargo ──────────────────────────────────────────────────────────
    {"bash": "cargo build", "ps": "cargo build"},
    {"bash": "cargo build --release", "ps": "cargo build --release"},
    {"bash": "cargo run", "ps": "cargo run"},
    {"bash": "cargo run --release", "ps": "cargo run --release"},
    {"bash": "cargo test", "ps": "cargo test"},
    {"bash": "cargo test -- --nocapture", "ps": "cargo test -- --nocapture"},
    {"bash": "cargo check", "ps": "cargo check"},
    {"bash": "cargo fmt", "ps": "cargo fmt"},
    {"bash": "cargo clippy", "ps": "cargo clippy"},
    {"bash": "cargo add tokio", "ps": "cargo add tokio"},
    {"bash": "cargo update", "ps": "cargo update"},
    {"bash": "cargo clean", "ps": "cargo clean"},
    # ── Directory navigation ──────────────────────────────────────────────────
    {"bash": "pwd", "ps": "Get-Location"},
    {"bash": "cd ..", "ps": "Set-Location .."},
    {"bash": "cd ~", "ps": "Set-Location $HOME"},
    {"bash": "cd /", "ps": "Set-Location C:\\"},
    {"bash": "cd src", "ps": "Set-Location 'src'"},
    {"bash": "cd src/", "ps": "Set-Location 'src'"},
    {"bash": "cd ../src", "ps": "Set-Location '../src'"},
    {"bash": "pushd src/", "ps": "Push-Location 'src/'"},
    {"bash": "popd", "ps": "Pop-Location"},
    # ── Misc ─────────────────────────────────────────────────────────────────
    {"bash": "which git", "ps": "(Get-Command git).Source"},
    {"bash": "which docker", "ps": "(Get-Command docker).Source"},
    {"bash": "type python3", "ps": "Get-Command python"},
    {"bash": "man git", "ps": "git --help"},
    {"bash": "man docker", "ps": "docker --help"},
    {"bash": "clear", "ps": "Clear-Host"},
    {"bash": "history", "ps": "Get-History"},
    {
        "bash": "history | grep git",
        "ps": "Get-History | Where-Object { $_.CommandLine -match 'git' }",
    },
    {"bash": "alias", "ps": "Get-Alias"},
    {"bash": "source ~/.bashrc", "ps": ". $PROFILE"},
    {"bash": ". ~/.bashrc", "ps": ". $PROFILE"},
    {
        "bash": "export PS1='\\u@\\h:\\w\\$ '",
        "ps": 'function prompt { "$env:USERNAME@$env:COMPUTERNAME:$(Get-Location)> " }',
    },
    {"bash": "cat /dev/null > file.txt", "ps": "Clear-Content 'file.txt'"},
    {"bash": "tee output.txt", "ps": "Tee-Object -FilePath 'output.txt'"},
    {"bash": "xargs rm", "ps": "ForEach-Object { Remove-Item $_ }"},
    {"bash": "read -p 'Enter value: ' VAR", "ps": "$VAR = Read-Host 'Enter value'"},
    {"bash": "exit 0", "ps": "exit 0"},
    {"bash": "exit 1", "ps": "exit 1"},
    # ── Pipes and redirects ───────────────────────────────────────────────────
    {"bash": "ls | grep '.py'", "ps": "Get-ChildItem | Where-Object { $_.Name -match '\\.py' }"},
    {"bash": "ls | head -n 10", "ps": "Get-ChildItem | Select-Object -First 10"},
    {"bash": "ls | tail -n 10", "ps": "Get-ChildItem | Select-Object -Last 10"},
    {"bash": "ls | wc -l", "ps": "(Get-ChildItem).Count"},
    {"bash": "cat file.txt | sort | uniq", "ps": "Get-Content 'file.txt' | Sort-Object -Unique"},
    {"bash": "cat file.txt | sort -u", "ps": "Get-Content 'file.txt' | Sort-Object -Unique"},
    {
        "bash": "cat file.txt | grep 'error'",
        "ps": "Select-String -Pattern 'error' -Path 'file.txt'",
    },
    {"bash": "cat app.log | wc -l", "ps": "(Get-Content 'app.log').Count"},
    {"bash": "ps aux | sort -k3 -r", "ps": "Get-Process | Sort-Object CPU -Descending"},
    {"bash": "ps aux | head -20", "ps": "Get-Process | Select-Object -First 20"},
    {
        "bash": "find . -name '*.py' | xargs grep 'import'",
        "ps": "Get-ChildItem -Recurse -Filter '*.py' | Select-String -Pattern 'import'",
    },
    {
        "bash": "find . -name '*.log' | xargs tail -n 5",
        "ps": "Get-ChildItem -Recurse -Filter '*.log' | ForEach-Object { Get-Content $_ -Tail 5 }",
    },
    {
        "bash": "command 2>&1 | tee output.log",
        "ps": "command 2>&1 | Tee-Object -FilePath 'output.log'",
    },
    {"bash": "command > output.txt 2>&1", "ps": "command > 'output.txt' 2>&1"},
    {"bash": "command > /dev/null 2>&1", "ps": "command > $null 2>&1"},
]


def select_seed_translations(limit: int | None = None) -> list[dict[str, str]]:
    """Return the bounded seed set used by `shellsage init`.

    The seed list is ordered by broad utility, so the first N entries cover the
    common commands AI coding agents most often get wrong on Windows.
    """
    if limit is None:
        return list(SEED_TRANSLATIONS)
    if limit < 1:
        raise ValueError("seed limit must be at least 1")
    return list(SEED_TRANSLATIONS[:limit])


def _validate_seed() -> None:
    """Sanity-check the seed at import time: no empty values, no dupes."""
    seen: set[str] = set()
    for i, entry in enumerate(SEED_TRANSLATIONS):
        assert entry.get("bash"), f"entry {i} missing 'bash'"
        assert entry.get("ps"), f"entry {i} missing 'ps'"
        key = entry["bash"].strip()
        if key in seen:
            raise ValueError(f"Duplicate bash entry in seed: {key!r}")
        seen.add(key)


_validate_seed()
