param(
    [string]$SourceDir = "",
    [string]$OutDir = "src/display/ui/bg"
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

# 1. Tìm thư mục chứa ảnh mặc định nếu không truyền tham số
if ([string]::IsNullOrWhiteSpace($SourceDir)) {
    $RepoSourcePictures = Join-Path $RepoRoot "config/xiaord-bg"
    if (Test-Path $RepoSourcePictures) {
        $SourceDir = $RepoSourcePictures
    } else {
        Write-Host "Please put your 'bg_user_defined.png' into 'config/xiaord-bg/' folder." -ForegroundColor Yellow
        return
    }
}

$SourcePath = Resolve-Path $SourceDir
$OutPath = Join-Path $RepoRoot $OutDir

# 2. Tìm chính xác file ảnh (Hỗ trợ cả bg_user_defined.png và bg_user_define.png để tránh lỗi đặt tên)
$Image = Get-ChildItem -LiteralPath $SourcePath | Where-Object { $_.Name -eq "bg_user_defined.png" -or $_.Name -eq "bg_user_define.png" } | Select-Object -First 1

if (-not $Image) {
    Write-Host "Error: Could not find 'bg_user_defined.png' in $SourcePath" -ForegroundColor Red
    return
}

# 3. Kiểm tra và cài đặt Pillow nếu thiếu
python -c "import PIL" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Pillow not found. Installing..." -ForegroundColor Cyan
    python -m pip install --user pillow
}

# 4. Chạy script chuyển đổi
Write-Host "Processing: $($Image.Name) -> bg_user_defined.c" -ForegroundColor Green

# Đã cập nhật tham số thứ hai thành "bg_user_defined" để đồng bộ
python (Join-Path $RepoRoot "tools/convert_xiaord_bg.py") `
    $Image.FullName `
    "bg_user_defined" `
    --out-dir $OutPath `
    --center-x "0.54" `
    --center-y "0.50" `
    --zoom "1.00"

Write-Host "Done! Build your firmware now with 'west build -p always' to see the new background." -ForegroundColor Green