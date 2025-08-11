Param(
  [string]$HostUrl = "http://127.0.0.1:8003"
)

Write-Host "[Day3] Using API: $HostUrl"

# 1) Build index by existing path (adjust path if needed)
$form = @{ 
  path = "uploads/keec101.pdf"; subject = "Economics"; chapter = "1"; chunk_size = 1200; chunk_overlap = 200; model = "all-MiniLM-L6-v2"
}
try {
  $res = Invoke-RestMethod -Method Post -Uri "$HostUrl/data/index" -Body $form -ContentType 'application/x-www-form-urlencoded'
  Write-Host "[Index] Namespace=$($res.namespace) Count=$($res.count) Chunks=$($res.chunks_path)"
} catch {
  Write-Host "[Index] Failed: $($_.Exception.Message)"; exit 1
}

# 2) Ask a question
$q = [System.Web.HttpUtility]::UrlEncode('What was the two-fold motive behind the deindustrialisation?')
try {
  $ask = Invoke-RestMethod -Method Get -Uri "$HostUrl/ask?q=$q&subject=Economics&chapter=1&k=4"
  Write-Host "[Ask] Namespace=$($ask.namespace) Results=$($ask.results.Count)"
  $ask.results | ForEach-Object {
    Write-Host "- p$($_.metadata.page_start)-$($_.metadata.page_end): $($_.text.Substring(0, [Math]::Min(120, $_.text.Length)))..."
  }
} catch {
  Write-Host "[Ask] Failed: $($_.Exception.Message)"; exit 1
}

Write-Host "[Day3] Done"
