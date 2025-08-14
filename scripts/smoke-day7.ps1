# Day 7 smoke: Practice sessions and Readiness summary
param(
  [string]$BaseUrl = "http://127.0.0.1:8003",
  [string]$Subject = "Economics",
  [string]$Chapter = "1",
  [int]$Total = 4,
  [int]$Mcq = 2,
  [int]$Short = 2
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail($msg) { Write-Error $msg; exit 1 }

Write-Host "[Day7] Health check $BaseUrl/health/"
try {
  $h = Invoke-RestMethod -Method GET -Uri "$BaseUrl/health/" -ErrorAction Stop
  if ($h.status -ne 'ok') { Write-Warning "Health returned unexpected payload: $($h | ConvertTo-Json -Depth 5)" }
}
catch { Fail "API not reachable at $BaseUrl. Start the server and retry. $_" }

# 1) Start a practice session
Write-Host "[Day7] POST /practice/start"
$startReq = @{ subject=$Subject; chapter=$Chapter; total=$Total; mcq=$Mcq; short=$Short } | ConvertTo-Json
$start = Invoke-RestMethod -Method Post -Uri "$BaseUrl/practice/start" -Body $startReq -ContentType 'application/json'
$sessionId = $start.sessionId
if (-not $sessionId) { Fail "No sessionId returned" }
Write-Host ("Session {0}: Q{1}/{2} type={3}" -f @($sessionId, ($start.index + 1), $start.total, $start.type))

# Helper to answer current question
function Submit-Answer($current) {
  if ($null -eq $current) { Fail "Current question payload is null" }
  $payload = @{ sessionId=$sessionId; type=$current.type }
  if ($current.type -eq 'mcq') {
    $payload.questionId = $current.questionId
    # naive: choose option 0
    $payload.selectedIndex = 0
  } elseif ($current.type -eq 'short') {
    # naive short answer
    $payload.answer = "This is a short answer"
  } else { Fail "Unknown question type: $($current.type)" }
  $json = ($payload | ConvertTo-Json)
  $sub = Invoke-RestMethod -Method Post -Uri "$BaseUrl/practice/submit" -Body $json -ContentType 'application/json'
  $res = $sub.submission
  if (-not $res) { Fail "No submission result returned" }
  if ($current.type -eq 'mcq') {
    Write-Host ("[MCQ] result={0} correctIndex={1}" -f $res.result,$res.correctIndex)
  } else {
    Write-Host ("[SHORT] result={0} score={1}" -f $res.result,$res.score)
  }
  return $sub
}

# Submit for first question
$sub1 = Submit-Answer $start

# 2) Next question
Write-Host "[Day7] POST /practice/next"
$nextReq = @{ sessionId=$sessionId } | ConvertTo-Json
$next = Invoke-RestMethod -Method Post -Uri "$BaseUrl/practice/next" -Body $nextReq -ContentType 'application/json'
Write-Host ("Next: Q{0}/{1} type={2}" -f @(($next.index + 1), $next.total, $next.type))

# Submit for second question
$sub2 = Submit-Answer $next

# 3) Optionally continue until done (we'll just demonstrate two)

# 4) Readiness: GET /eval/summary
Write-Host "[Day7] GET /eval/summary"
try {
  $eval = Invoke-RestMethod -Method Get -Uri "$BaseUrl/eval/summary"
  Write-Host ("Eval: total={0} hit={1:P1} ans={2:P1} cite={3:P1}" -f @($eval.total_questions, $eval.hit_rate, $eval.answer_rate, $eval.citation_rate))
} catch {
  Write-Warning "Eval summary not available: $($_.Exception.Message)"
}

Write-Host "[Day7] Smoke complete"
