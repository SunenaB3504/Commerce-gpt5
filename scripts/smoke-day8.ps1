param(
  [string]$Base = 'http://127.0.0.1:8000',
  [string]$Subject = 'Economics',
  [string]$Chapter = '3',
  [string]$PdfPath = 'uploads/18a9c7c4-0587-4e8d-a951-813338ed4822_keec101.pdf',
  [int]$K = 8,
  [string]$Retriever = 'tfidf'
)

Write-Host "[Day8] Smoke: upload->index->ask against $Base"

# Upload with auto-index
try {
  $form = @{ subject=$Subject; chapter=$Chapter; auto_index='true'; reset='false' }
  $file = Get-Item $PdfPath -ErrorAction Stop
  $resp = Invoke-WebRequest -Uri "$Base/data/upload" -Method Post -Form @{ file=$file; subject=$Subject; chapter=$Chapter; auto_index='true'; reset='false' }
  Write-Host "Upload status: $($resp.StatusCode)"
  $json = $resp.Content | ConvertFrom-Json
  Write-Host "Namespace: $($json.namespace) Count: $($json.index_count)"
}
catch {
  Write-Host "Upload failed: $($_.Exception.Message)" -ForegroundColor Red
}

# Ask
try {
  $q = [System.Web.HttpUtility]::UrlEncode('Ways a partner can retire from the firm')
  $askUrl = "$Base/ask?q=$q&subject=$Subject&chapter=$Chapter&k=$K&retriever=$Retriever"
  $aresp = Invoke-WebRequest -Uri $askUrl -Method Get
  $ajs = $aresp.Content | ConvertFrom-Json
  Write-Host "Answer: $($ajs.answer)"
  if ($ajs.citations) { $ajs.citations | ForEach-Object { Write-Host ("p{0}-{1} {2}" -f $_.page_start,$_.page_end,$_.filename) } }
}
catch {
  Write-Host "Ask failed: $($_.Exception.Message)" -ForegroundColor Red
}
