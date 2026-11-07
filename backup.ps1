param([string]$Note = "")
$root = $PSScriptRoot
$ts = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$dest = Join-Path $root "backups\$ts"
New-Item -ItemType Directory -Path $dest -Force | Out-Null
$files = @("admin.html", "Acceleratorares.html", "vercel.json", "BAN-GIAO-CHO-CHAT-MOI.txt", "yt-server\server.js")
foreach ($f in $files) {
  $p = Join-Path $root $f
  if (Test-Path -LiteralPath $p) { Copy-Item -LiteralPath $p -Destination $dest }
}
if ($Note) { Set-Content -LiteralPath (Join-Path $dest "GHI-CHU.txt") -Value $Note -Encoding UTF8 }
Write-Output "Da sao luu ban cu -> $dest"
