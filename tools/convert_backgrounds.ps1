param(
    [string]$SourceDir = "",
    [string]$OutDir = "src/display/ui/bg"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

# 1. Tự động tìm thư mục chứa ảnh nếu không truyền vào
if ([string]::IsNullOrWhiteSpace($SourceDir)) {
    $RepoSourcePictures = Join-Path $RepoRoot "config/xiaord-bg"
    if (Test-Path $RepoSourcePictures) {
        $SourceDir = $RepoSourcePictures
    } else {
        throw "Folder 'config/xiaord-bg' not found. Please provide SourceDir."
    }
}

$SourcePath = Resolve-Path $SourceDir
$OutPath = Join-Path $RepoRoot $OutDir

# 2. Tìm chính xác file bg_user_define.png
$Image = Get-ChildItem -LiteralPath $SourcePath | Where-Object { $_.Name -eq "bg_user_define.png" }

if (-not $Image) {
    throw "Error: 'bg_user_define.png' not found in $SourcePath"
}

# 3. Đảm bảo Pillow đã được cài đặt
python -c "import PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing Pillow..."
    python -m pip install --user pillow
}

# 4. Thực hiện chuyển đổi
Write-Host "Processing: $($Image.FullName) -> bg_user_define.c"

python (Join-Path $RepoRoot "tools/convert_xiaord_bg.py") `
    $Image.FullName `
    --out-dir $OutPath `
    --center-x "0.54" `
    --center-y "0.50" `
    --zoom "1.00"

Write-Host "Success! Firmware will use the new background from bg_user_define.c"