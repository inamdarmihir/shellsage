"""
Seed translations loaded on `shellsage init`.

These provide day-one coverage before any real commands have been run.
Format: {"bash": "...", "ps": "..."}
"""

SEED_TRANSLATIONS = [
    # listing
    {"bash": "ls", "ps": "Get-ChildItem"},
    {"bash": "ls -la", "ps": "Get-ChildItem -Force"},
    {"bash": "ls -l", "ps": "Get-ChildItem"},
    {"bash": "ls -a", "ps": "Get-ChildItem -Force"},
    {"bash": "ls *.py", "ps": "Get-ChildItem *.py"},
    # find
    {"bash": "find . -name '*.py'", "ps": "Get-ChildItem -Recurse -Filter '*.py'"},
    {"bash": "find . -name '*.js'", "ps": "Get-ChildItem -Recurse -Filter '*.js'"},
    {"bash": "find . -name '*.ts'", "ps": "Get-ChildItem -Recurse -Filter '*.ts'"},
    {"bash": "find . -type f -name '*.txt'", "ps": "Get-ChildItem -Recurse -File -Filter '*.txt'"},
    {"bash": "find . -type d", "ps": "Get-ChildItem -Recurse -Directory"},
    # grep
    {"bash": "grep -r 'TODO' .", "ps": "Get-ChildItem -Recurse | Select-String -Pattern 'TODO'"},
    {
        "bash": "grep -rn 'import' src/",
        "ps": "Get-ChildItem -Recurse 'src/' | Select-String -Pattern 'import'",
    },
    {"bash": "grep 'error' log.txt", "ps": "Select-String -Pattern 'error' -Path 'log.txt'"},
    # cat / head / tail
    {"bash": "cat README.md", "ps": "Get-Content 'README.md'"},
    {"bash": "cat package.json", "ps": "Get-Content 'package.json'"},
    {"bash": "head -n 20 file.txt", "ps": "Get-Content 'file.txt' -TotalCount 20"},
    {"bash": "tail -n 50 file.log", "ps": "Get-Content 'file.log' -Tail 50"},
    {"bash": "tail -f server.log", "ps": "Get-Content -Wait 'server.log'"},
    # mkdir / rm / cp / mv
    {"bash": "mkdir -p src/utils", "ps": "New-Item -ItemType Directory -Force -Path 'src/utils'"},
    {"bash": "mkdir -p dist", "ps": "New-Item -ItemType Directory -Force -Path 'dist'"},
    {"bash": "rm -rf node_modules", "ps": "Remove-Item -Recurse -Force 'node_modules'"},
    {"bash": "rm -rf dist/", "ps": "Remove-Item -Recurse -Force 'dist/'"},
    {"bash": "rm -f output.log", "ps": "Remove-Item -Force 'output.log'"},
    {"bash": "cp -r src/ backup/", "ps": "Copy-Item -Recurse 'src/' 'backup/'"},
    {"bash": "mv old.txt new.txt", "ps": "Move-Item 'old.txt' 'new.txt'"},
    # env / export
    {"bash": "export NODE_ENV=production", "ps": "$env:NODE_ENV = 'production'"},
    {"bash": "export DEBUG=true", "ps": "$env:DEBUG = 'true'"},
    {"bash": "export PORT=3000", "ps": "$env:PORT = '3000'"},
    {"bash": "printenv PATH", "ps": "$env:PATH"},
    {"bash": "env", "ps": "Get-ChildItem Env:"},
    # process
    {"bash": "ps aux", "ps": "Get-Process"},
    {"bash": "ps aux | grep node", "ps": "Get-Process | Where-Object { $_.Name -match 'node' }"},
    {"bash": "kill -9 1234", "ps": "Stop-Process -Id 1234 -Force"},
    # network
    {"bash": "curl -s https://api.github.com", "ps": "Invoke-RestMethod 'https://api.github.com'"},
    {"bash": "curl https://example.com", "ps": "Invoke-WebRequest -Uri 'https://example.com'"},
    {
        "bash": "wget https://example.com/file.zip",
        "ps": "Invoke-WebRequest -Uri 'https://example.com/file.zip' -OutFile './file.zip'",
    },
    # pipes
    {"bash": "cat file.txt | wc -l", "ps": "(Get-Content 'file.txt').Count"},
    {"bash": "ls | sort", "ps": "Get-ChildItem | Sort-Object"},
    {"bash": "ls | sort -u", "ps": "Get-ChildItem | Sort-Object -Unique"},
    # python / node common patterns
    {"bash": "python3 -m pytest", "ps": "python -m pytest"},
    {
        "bash": "python3 -m pip install -r requirements.txt",
        "ps": "python -m pip install -r requirements.txt",
    },
    {"bash": "python3 script.py", "ps": "python script.py"},
    {
        "bash": "chmod +x script.sh",
        "ps": "# chmod not needed in PowerShell — use Set-ExecutionPolicy or .ps1 files",
    },
    {"bash": "which python3", "ps": "Get-Command python"},
    {"bash": "which node", "ps": "Get-Command node"},
    # git (same on both but often typed wrong)
    {"bash": "git log --oneline -10", "ps": "git log --oneline -10"},
    {"bash": "git diff --stat", "ps": "git diff --stat"},
    # docker
    {"bash": "docker ps -a", "ps": "docker ps -a"},
    {"bash": "docker logs -f container_name", "ps": "docker logs -f container_name"},
    # text
    {"bash": "echo $PATH", "ps": "$env:PATH"},
    {"bash": "echo 'hello world'", "ps": "Write-Output 'hello world'"},
    {"bash": "wc -l file.txt", "ps": "(Get-Content 'file.txt').Count"},
    # directory navigation
    {"bash": "pwd", "ps": "Get-Location"},
    {"bash": "cd ..", "ps": "Set-Location .."},
    {"bash": "cd ~", "ps": "Set-Location $HOME"},
    # misc
    {"bash": "touch file.txt", "ps": "New-Item -ItemType File 'file.txt'"},
    {"bash": "ln -s src dest", "ps": "New-Item -ItemType SymbolicLink -Name 'dest' -Target 'src'"},
    {"bash": "df -h", "ps": "Get-PSDrive"},
    {
        "bash": "du -sh .",
        "ps": "(Get-ChildItem -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB",
    },
]
