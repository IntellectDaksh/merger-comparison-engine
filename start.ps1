$ErrorActionPreference = 'Stop'
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Push-Location $PSScriptRoot
try {
    if ($pythonCommand) { & $pythonCommand.Source app.py }
    elseif (Test-Path -LiteralPath $bundledPython) { & $bundledPython app.py }
    else { throw 'Install Python 3.10 or newer, then run python app.py from this folder.' }
}
finally { Pop-Location }
