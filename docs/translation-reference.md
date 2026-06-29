# Translation Reference

The rule engine handles these commands immediately, with zero database required.

!!! info "Loading the full corpus"
    `shellsage init` loads 75 curated examples by default. Run `shellsage init --all` to load all 400+ seed translations into SQLite for lookup fallback.

---

## File Listing

| Bash | PowerShell |
|---|---|
| `ls` | `Get-ChildItem` |
| `ls -la` | `Get-ChildItem -Force` |
| `ls -l` | `Get-ChildItem \| Format-List` |
| `ls -R` | `Get-ChildItem -Recurse` |
| `ls *.py` | `Get-ChildItem *.py` |
| `ls -la src/` | `Get-ChildItem -Force 'src/'` |
| `ls ~` | `Get-ChildItem $HOME` |

---

## Find / Locate

| Bash | PowerShell |
|---|---|
| `find . -name '*.py'` | `Get-ChildItem -Recurse -Filter '*.py'` |
| `find . -type f` | `Get-ChildItem -Recurse -File` |
| `find . -type d` | `Get-ChildItem -Recurse -Directory` |
| `find . -type f -name '*.log'` | `Get-ChildItem -Recurse -File -Filter '*.log'` |
| `find src/ -name '*.py'` | `Get-ChildItem -Path 'src/' -Recurse -Filter '*.py'` |
| `find . -mtime -7` | `Get-ChildItem -Recurse \| Where-Object { $_.LastWriteTime -gt (Get-Date).AddDays(-7) }` |
| `find . -size +1M` | `Get-ChildItem -Recurse \| Where-Object { $_.Length -gt 1MB }` |
| `find . -name '*.tmp' -delete` | `Get-ChildItem -Recurse -Filter '*.tmp' \| Remove-Item -Force` |
| `find . -name '*.pyc' -delete` | `Get-ChildItem -Recurse -Filter '*.pyc' \| Remove-Item -Force` |

---

## Grep / Search

| Bash | PowerShell |
|---|---|
| `grep 'error' app.log` | `Select-String -Pattern 'error' -Path 'app.log'` |
| `grep -r 'TODO' .` | `Get-ChildItem -Recurse \| Select-String -Pattern 'TODO'` |
| `grep -rn 'import' src/` | `Get-ChildItem -Recurse 'src/' \| Select-String -Pattern 'import'` |
| `grep -i 'error' app.log` | `Select-String -Pattern 'error' -Path 'app.log' -CaseSensitive:$false` |
| `grep -v 'debug' app.log` | `Get-Content 'app.log' \| Where-Object { $_ -notmatch 'debug' }` |
| `grep -c 'error' app.log` | `(Select-String -Pattern 'error' -Path 'app.log').Count` |
| `grep -l 'TODO' *.py` | `Select-String -Pattern 'TODO' -Path '*.py' \| Select-Object -ExpandProperty Path -Unique` |
| `grep 'error' *.log` | `Select-String -Pattern 'error' -Path '*.log'` |
| `grep -r 'password' . --include='*.py'` | `Get-ChildItem -Recurse -Filter '*.py' \| Select-String -Pattern 'password'` |

---

## View Files

| Bash | PowerShell |
|---|---|
| `cat README.md` | `Get-Content 'README.md'` |
| `cat file1.txt file2.txt` | `Get-Content 'file1.txt', 'file2.txt'` |
| `head -n 20 file.txt` | `Get-Content 'file.txt' -TotalCount 20` |
| `tail -n 50 app.log` | `Get-Content 'app.log' -Tail 50` |
| `tail -f server.log` | `Get-Content -Wait 'server.log'` |

---

## File Management

| Bash | PowerShell |
|---|---|
| `mkdir -p src/utils` | `New-Item -ItemType Directory -Force -Path 'src/utils'` |
| `rm -rf node_modules` | `Remove-Item -Recurse -Force 'node_modules'` |
| `rm -rf dist/` | `Remove-Item -Recurse -Force 'dist/'` |
| `rm -f output.log` | `Remove-Item -Force 'output.log'` |
| `cp -r src/ backup/` | `Copy-Item -Recurse 'src/' 'backup/'` |
| `cp config.json config.json.bak` | `Copy-Item 'config.json' 'config.json.bak'` |
| `mv old.txt new.txt` | `Move-Item 'old.txt' 'new.txt'` |
| `touch .gitkeep` | `New-Item -ItemType File -Force '.gitkeep'` |
| `ln -s src dest` | `New-Item -ItemType SymbolicLink -Name 'dest' -Target 'src'` |

---

## Text Processing

| Bash | PowerShell |
|---|---|
| `wc -l file.txt` | `(Get-Content 'file.txt').Count` |
| `sort file.txt` | `Get-Content 'file.txt' \| Sort-Object` |
| `sort -u file.txt` | `Get-Content 'file.txt' \| Sort-Object -Unique` |
| `sort -r file.txt` | `Get-Content 'file.txt' \| Sort-Object -Descending` |
| `sort file.txt \| uniq -c` | `Get-Content 'file.txt' \| Group-Object \| Select-Object Count, Name` |
| `sed -i 's/foo/bar/g' file.txt` | `(Get-Content 'file.txt') -replace 'foo','bar' \| Set-Content 'file.txt'` |
| `sed '/^#/d' file.txt` | `Get-Content 'file.txt' \| Where-Object { $_ -notmatch '^#' }` |
| `awk '{print $1}' file.txt` | `Get-Content 'file.txt' \| ForEach-Object { ($_ -split '\s+')[0] }` |

---

## Echo / Redirect

| Bash | PowerShell |
|---|---|
| `echo 'hello world'` | `Write-Output 'hello world'` |
| `echo $PATH` | `$env:PATH` |
| `echo $HOME` | `$env:USERPROFILE` |
| `echo 'line' > file.txt` | `Set-Content 'file.txt' 'line'` |
| `echo 'line' >> file.txt` | `Add-Content 'file.txt' 'line'` |

---

## Environment Variables

| Bash | PowerShell |
|---|---|
| `export NODE_ENV=production` | `$env:NODE_ENV = 'production'` |
| `export PORT=3000` | `$env:PORT = '3000'` |
| `export DATABASE_URL=postgres://localhost/db` | `$env:DATABASE_URL = 'postgres://localhost/db'` |
| `unset NODE_ENV` | `Remove-Item Env:\NODE_ENV` |
| `env` | `Get-ChildItem Env:` |
| `printenv PATH` | `$env:PATH` |

---

## Process Management

| Bash | PowerShell |
|---|---|
| `ps aux` | `Get-Process` |
| `ps aux \| grep node` | `Get-Process \| Where-Object { $_.Name -match 'node' }` |
| `pgrep python` | `Get-Process -Name '*python*'` |
| `pkill node` | `Stop-Process -Name 'node' -Force` |
| `kill -9 1234` | `Stop-Process -Id 1234 -Force` |
| `killall python` | `Stop-Process -Name 'python' -Force` |
| `sleep 5` | `Start-Sleep 5` |
| `nohup python app.py &` | `Start-Process -NoNewWindow python -ArgumentList 'app.py' -RedirectStandardOutput 'nohup.out'` |

---

## Network

| Bash | PowerShell |
|---|---|
| `curl https://example.com` | `Invoke-WebRequest -Uri 'https://example.com'` |
| `curl -s https://api.github.com` | `Invoke-RestMethod 'https://api.github.com'` |
| `curl -o file.zip https://example.com/a.zip` | `Invoke-WebRequest -Uri 'https://example.com/a.zip' -OutFile 'file.zip'` |
| `curl -X POST URL -d '{"k":"v"}'` | `Invoke-RestMethod -Method POST -Uri URL -Body '{"k":"v"}' -ContentType 'application/json'` |
| `curl -H 'Authorization: Bearer TOKEN' URL` | `Invoke-RestMethod -Uri URL -Headers @{ Authorization = 'Bearer TOKEN' }` |
| `wget https://example.com/file.zip` | `Invoke-WebRequest -Uri 'https://example.com/file.zip' -OutFile 'file.zip'` |
| `ping google.com` | `Test-Connection -ComputerName 'google.com'` |
| `ping -c 4 google.com` | `Test-Connection -ComputerName 'google.com' -Count 4` |
| `netstat -tulpn` | `Get-NetTCPConnection \| Where-Object { $_.State -eq 'Listen' }` |
| `nslookup google.com` | `Resolve-DnsName 'google.com'` |

---

## Archive / Compression

| Bash | PowerShell |
|---|---|
| `tar -czf archive.tar.gz dist/` | `Compress-Archive -Path 'dist/' -DestinationPath 'archive.zip'` |
| `tar -xzf archive.tar.gz` | `Expand-Archive -Path 'archive.zip' -DestinationPath '.'` |
| `tar -xzf archive.tar.gz -C out/` | `Expand-Archive -Path 'archive.zip' -DestinationPath 'out/'` |
| `zip -r archive.zip src/` | `Compress-Archive -Path 'src/' -DestinationPath 'archive.zip'` |
| `unzip archive.zip -d output/` | `Expand-Archive -Path 'archive.zip' -DestinationPath 'output/'` |

---

## Disk / System Info

| Bash | PowerShell |
|---|---|
| `df -h` | `Get-PSDrive -PSProvider FileSystem` |
| `du -sh .` | `(Get-ChildItem -Recurse \| Measure-Object -Property Length -Sum).Sum / 1MB` |
| `du -sh node_modules/` | `(Get-ChildItem -Recurse 'node_modules/' \| Measure-Object -Property Length -Sum).Sum / 1MB` |
| `uname -a` | `Get-ComputerInfo \| Select-Object WindowsProductName, WindowsVersion` |
| `hostname` | `$env:COMPUTERNAME` |
| `whoami` | `$env:USERNAME` |
| `date` | `Get-Date` |
| `date '+%Y-%m-%d'` | `Get-Date -Format 'yyyy-MM-dd'` |
| `uptime` | `(Get-Date) - (Get-CimInstance Win32_OperatingSystem).LastBootUpTime` |

---

## Permissions

| Bash | PowerShell |
|---|---|
| `chmod +x script.sh` | `# Rename to script.ps1 or use Set-ExecutionPolicy` |
| `chmod 755 dir/` | `# Use icacls for Windows ACL management` |
| `chown user file` | `# Use icacls: icacls 'file' /setowner 'user'` |
| `sudo command` | `# Run PowerShell as Administrator, then: command` |

---

## Python

| Bash | PowerShell |
|---|---|
| `python3 script.py` | `python script.py` |
| `python3 -m pytest` | `python -m pytest` |
| `python3 -m pytest -v` | `python -m pytest -v` |
| `python3 -m pip install -r requirements.txt` | `python -m pip install -r requirements.txt` |
| `python3 -m pip install -e .` | `python -m pip install -e .` |
| `python3 -m venv .venv` | `python -m venv .venv` |
| `source .venv/bin/activate` | `.venv\Scripts\Activate.ps1` |
| `python3 -m pip freeze > requirements.txt` | `python -m pip freeze \| Set-Content 'requirements.txt'` |
| `which python3` | `(Get-Command python).Source` |

---

## Node.js / npm

| Bash | PowerShell |
|---|---|
| `npm install` | `npm install` |
| `npm install package` | `npm install package` |
| `npm run build` | `npm run build` |
| `npm run dev` | `npm run dev` |
| `npm test` | `npm test` |
| `npx tsc` | `npx tsc` |
| `yarn install` | `yarn install` |
| `yarn add package` | `yarn add package` |

---

## Docker

| Bash | PowerShell |
|---|---|
| `docker ps -a` | `docker ps -a` |
| `docker build -t myapp .` | `docker build -t myapp .` |
| `docker run -d -p 8080:8080 myapp` | `docker run -d -p 8080:8080 myapp` |
| `docker exec -it mycontainer bash` | `docker exec -it mycontainer bash` |
| `docker logs -f mycontainer` | `docker logs -f mycontainer` |
| `docker-compose up -d` | `docker-compose up -d` |
| `docker-compose down` | `docker-compose down` |
| `docker system prune -f` | `docker system prune -f` |

---

## Git

Git commands are **identical** on all platforms — ShellSage passes them through unchanged.

| Bash / PowerShell |
|---|
| `git init` · `git clone URL` · `git status` · `git add .` |
| `git commit -m 'message'` · `git push origin main` · `git pull` |
| `git checkout -b feature/name` · `git merge branch` · `git rebase main` |
| `git log --oneline -10` · `git diff --stat` · `git stash` |

---

## Directory Navigation

| Bash | PowerShell |
|---|---|
| `pwd` | `Get-Location` |
| `cd src/` | `Set-Location 'src/'` |
| `cd ..` | `Set-Location ..` |
| `cd ~` | `Set-Location $HOME` |
| `pushd src/` | `Push-Location 'src/'` |
| `popd` | `Pop-Location` |

---

## Pipes and Redirects

| Bash | PowerShell |
|---|---|
| `ls \| grep '.py'` | `Get-ChildItem \| Where-Object { $_.Name -match '\.py' }` |
| `ls \| wc -l` | `(Get-ChildItem).Count` |
| `cat file.txt \| sort \| uniq` | `Get-Content 'file.txt' \| Sort-Object -Unique` |
| `find . -name '*.py' \| xargs grep 'import'` | `Get-ChildItem -Recurse -Filter '*.py' \| Select-String -Pattern 'import'` |
| `command > /dev/null 2>&1` | `command > $null 2>&1` |
