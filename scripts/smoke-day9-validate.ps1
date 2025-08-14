param(
  [string]$BaseUrl = 'http://127.0.0.1:8003',
  [string]$Subject = 'Economics',
  [string]$Chapter = '1'
)

Write-Host "[Day9] Smoke: /answer/validate against curated question"
$q = 'what is inflation'
$good = 'Inflation is a sustained rise in the general price level of goods and services in an economy over time reducing purchasing power of money.'
$partial = 'Prices rise over time'

function Invoke-Validate($question, $answer) {
  $payload = @{ question=$question; userAnswer=$answer; subject=$Subject; chapter=$Chapter } | ConvertTo-Json
  return Invoke-RestMethod -Method Post -Uri "$BaseUrl/answer/validate" -Body $payload -ContentType 'application/json'
}

try {
  $rGood = Invoke-Validate $q $good
  Write-Host ("Good -> result={0} score={1}" -f $rGood.result,$rGood.score)
  if ($rGood.result -eq 'incorrect') { Write-Warning 'Expected better than incorrect for good answer' }
  $rPartial = Invoke-Validate $q $partial
  Write-Host ("Partial -> result={0} score={1}" -f $rPartial.result,$rPartial.score)
} catch {
  Write-Error "Validation smoke failed: $_"; exit 1
}

Write-Host '[Day9] Done'
