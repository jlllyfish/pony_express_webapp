param([string]$config = "contrat_pedagogique", [switch]$generer, [switch]$colonnes, [string]$tables = "")

Set-Location $PSScriptRoot
# le code du projet (src\pony_express) est trouvé sans installation préalable
$env:PYTHONPATH = "$PSScriptRoot\src"
Get-Content .env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object {
    $k, $v = $_ -split '=', 2
    Set-Item "env:$($k.Trim())" $v.Trim()
}

if ($colonnes) {
    .\.venv\Scripts\python.exe lister_colonnes.py $tables
} elseif ($generer) {
    .\.venv\Scripts\python.exe "src\pony_express\templates\$config.py"
    Invoke-Item generated
} else {
    .\.venv\Scripts\python.exe check_mapping.py $config --limit 0 --compile
}