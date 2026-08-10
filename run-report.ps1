param(
  [Parameter(Mandatory=$true)][string]$Birth,
  [Parameter(Mandatory=$true)][string]$Timezone,
  [Parameter(Mandatory=$true)][double]$Latitude,
  [Parameter(Mandatory=$true)][double]$Longitude,
  [Parameter(Mandatory=$true)][ValidateSet('M','F')][string]$Gender,
  [Parameter(Mandatory=$true)][string]$CaseDir,
  [string]$AsOf = (Get-Date -Format 'yyyy-MM-dd'),
  [int]$StartYear = 2026,
  [ValidateSet('standard','deep')][string]$Mode = 'deep',
  [ValidateSet('zh-TW','en')][string]$Language = 'zh-TW',
  [string]$Python = $env:FOURPIE_PYTHON,
  [switch]$Force
)
$ErrorActionPreference = 'Stop'
$previousPythonUtf8 = $env:PYTHONUTF8
$env:PYTHONUTF8 = '1'
Push-Location -LiteralPath $PSScriptRoot
try {
  $venvPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
  $ready = $false
  if (Test-Path -LiteralPath $venvPython) {
    & $venvPython scripts\4pie.py doctor *> $null
    $ready = ($LASTEXITCODE -eq 0)
  }
  if (-not $ready) {
    Write-Host '4PIE_ENV_NOT_READY running setup once; allow this command up to 15 minutes.'
    if ($Python) { & .\setup.ps1 -Python $Python } else { & .\setup.ps1 }
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
  } else {
    Write-Host '4PIE_ENV_REUSED doctor=ok setup=skipped'
  }
  $prepareArgs = @('scripts\4pie.py','prepare','--case-dir',$CaseDir,'--datetime',$Birth,'--timezone',$Timezone,'--lat',[string]$Latitude,'--lon',[string]$Longitude,'--gender',$Gender,'--as-of',$AsOf,'--start-year',[string]$StartYear,'--mode',$Mode,'--language',$Language)
  if ($Force) { $prepareArgs += '--force' }
  & $venvPython @prepareArgs
  exit $LASTEXITCODE
} finally {
  $env:PYTHONUTF8 = $previousPythonUtf8
  Pop-Location
}
