param([int]$Port = 8081)
$root = $PSScriptRoot
Set-Location -LiteralPath $root
$url = "http://127.0.0.1:$Port/Acceleratorares.html"
Write-Output "Ban demo LOCAL dang chay (Ctrl+C de dung):"
Write-Output "  Trang chinh : $url"
Write-Output "  Quan tri    : http://127.0.0.1:$Port/admin.html"
Start-Process $url
python -m http.server $Port --bind 127.0.0.1
