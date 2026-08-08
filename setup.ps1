param([string]$Python = $env:FOURPIE_PYTHON)
$ErrorActionPreference = 'Stop'
$previousPythonUtf8 = $env:PYTHONUTF8
$env:PYTHONUTF8 = '1'
# Prefer python.exe: some Windows py.exe releases corrupt non-ASCII project paths.
Push-Location -LiteralPath $PSScriptRoot
try {
Write-Host '4PIE_SETUP_START first install may take 2-10 minutes; automation tools should allow at least 15 minutes.'
Write-Host 'Do not start setup again after an outer-tool timeout. The active installer is protected by .setup.lock.'
if ($Python) {
  & $Python -c "import runpy; runpy.run_path('scripts/bootstrap.py', run_name='__main__')"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
  & python -c "import runpy; runpy.run_path('scripts/bootstrap.py', run_name='__main__')"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  & py -3 -c "import runpy; runpy.run_path('scripts/bootstrap.py', run_name='__main__')"
} else {
  throw 'Python is required. The installer will select a compatible Python 3.8-3.13 runtime.'
}
$code = $LASTEXITCODE
} finally {
  $env:PYTHONUTF8 = $previousPythonUtf8
  Pop-Location
}
exit $code
