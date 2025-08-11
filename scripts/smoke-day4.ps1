# Day 4 smoke: ask with synthesis and stream
param(
  [string]$BaseUrl = "http://127.0.0.1:8003",
  [string]$Subject = "Economics",
  [string]$Chapter = "1",
  [string]$Q = "two-fold motive behind the deindustrialisation",
  [int]$K = 6
)

Write-Host "Health check $BaseUrl/health/"
try {
  $h = Invoke-RestMethod -Method GET -Uri "$BaseUrl/health/" -ErrorAction Stop
  if ($h.status -ne 'ok') { Write-Warning "Health returned unexpected payload: $($h | ConvertTo-Json -Depth 5)" }
}
catch {
  Write-Error "API not reachable at $BaseUrl. Start the server and retry. $_"
  exit 1
}

Write-Host "GET $BaseUrl/ask"
$r = Invoke-RestMethod -Method GET -Uri "$BaseUrl/ask?q=$( [uri]::EscapeDataString($Q) )&subject=$Subject&chapter=$Chapter&k=$K&answer_synthesis=true"
"Namespace: {0}" -f $r.namespace
"Answer:\n{0}" -f $r.answer
"Citations:" 
$r.citations | ForEach-Object { "- p$($_.page_start)-$($_.page_end)  $($_.filename)" }
"Top passages:" 
$r.results | Select-Object -First 3 | ForEach-Object {
  $p = "p$($_.metadata.page_start)-$($_.metadata.page_end)"
  $t = if ($_.text.Length -gt 160) { $_.text.Substring(0,160) + '.' } else { $_.text }
  "{0}  dist={1:N3}  {2}" -f $p, $_.distance, $t
}
