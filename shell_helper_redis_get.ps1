$key = "stock:name:600519"
$client = New-Object System.Net.Sockets.TcpClient
$client.Connect("naemini.local", 6379)
$stream = $client.GetStream()
$writer = New-Object System.IO.StreamWriter($stream)
$writer.AutoFlush = $true

# RESP: *2 $3 GET $16 stock:name:600519
$cmd = "*2`r`n`$3`r`nGET`r`n`$" + $key.Length + "`r`n" + $key + "`r`n"
$writer.Write($cmd)

Start-Sleep -Milliseconds 100
$reader = New-Object System.IO.StreamReader($stream)
$response = $reader.ReadLine()
Write-Host "Response: $response"

$client.Close()
