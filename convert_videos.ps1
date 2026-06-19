# Convert all MP4 files in current folder to 720p

$files = Get-ChildItem -Filter *.mp4

if ($files.Count -eq 0) {
    Write-Host "No MP4 files found in this folder." -ForegroundColor Yellow
    exit
}

foreach ($file in $files) {

    # Skip already converted 720p files
    if ($file.BaseName -match '_720$') {
        Write-Host "Skipping already converted file: $($file.Name)" -ForegroundColor Yellow
        continue
    }

    # Try to get number from filename
    # Works for: "Session 1", "Session 2", "1-Live Session", "2-Live Career"
    if ($file.BaseName -match '(\d+)') {
        $num = $matches[1].PadLeft(2, '0')
    }
    else {
        $num = "00"
    }

    # Clean file name
    $cleanName = $file.BaseName `
        -replace '[^\w\s-]', '' `
        -replace '\s+', '_'

    $newName = "$num`_$cleanName`_720.mp4"

    Write-Host "Processing: $($file.Name)" -ForegroundColor Cyan
    Write-Host "Output: $newName" -ForegroundColor Green

    ffmpeg -i "$($file.FullName)" `
        -vf scale=-2:720 `
        -c:v libx264 `
        -preset slow `
        -crf 24 `
        -c:a aac `
        -b:a 96k `
        -movflags +faststart `
        "$newName"
}

Write-Host "All videos processed." -ForegroundColor Green