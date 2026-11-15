# Requires Windows PowerShell 5.1 or newer.
# Copies 漢字通 into the Weasel user directory and registers the schema.
# Does not deploy. Redeploy from the Weasel menu after this script finishes.
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$rime = Join-Path $env:APPDATA "Rime"
$utf8 = New-Object System.Text.UTF8Encoding $false

New-Item -ItemType Directory -Force -Path $rime | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $rime "lua") | Out-Null

$names = @(
    "hanzi_tong.schema.yaml",
    "hanzi_tong.dict.yaml",
    "hanzi_tong.pinyin.dict.yaml",
    "hanzi_tong.jyutping.dict.yaml",
    "hanzi_tong.poj.dict.yaml",
    "hanzi_tong.hanja.dict.yaml",
    "hanzi_tong.kanji.dict.yaml"
)

foreach ($name in $names) {
    $source = Join-Path $root $name
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Missing $source. Run tools/build_dictionaries.py first."
    }
    Copy-Item -LiteralPath $source -Destination (Join-Path $rime $name) -Force
}

Copy-Item -LiteralPath (Join-Path $root "lua\hanzi_tong.lua") -Destination (Join-Path $rime "lua\hanzi_tong.lua") -Force

$custom = Join-Path $rime "default.custom.yaml"
if (Test-Path -LiteralPath $custom) {
    $customText = [System.IO.File]::ReadAllText($custom, $utf8)
} else {
    $customText = ""
}

if ($customText -notmatch "schema:\s*hanzi_tong") {
    $block = "  schema_list/+:`r`n    - schema: hanzi_tong"
    if ($customText -match "(?m)^patch:[ \t]*$") {
        $customText = [regex]::Replace($customText, "(?m)^patch:[ \t]*$", "patch:`r`n$block", 1)
    } else {
        if ($customText.Length -gt 0 -and -not $customText.EndsWith("`n")) {
            $customText += "`r`n"
        }
        $customText += "patch:`r`n$block`r`n"
    }
    [System.IO.File]::WriteAllText($custom, $customText, $utf8)
}

$luaPath = Join-Path $rime "rime.lua"
$hook = [System.IO.File]::ReadAllText((Join-Path $root "rime.lua"), $utf8).TrimEnd() + "`r`n"
if (-not (Test-Path -LiteralPath $luaPath)) {
    [System.IO.File]::WriteAllText($luaPath, $hook, $utf8)
} else {
    $existingBytes = [System.IO.File]::ReadAllBytes($luaPath)
    $existingAscii = [System.Text.Encoding]::ASCII.GetString($existingBytes)
    if ($existingAscii -notlike "*hanzi_tong_balance*") {
        $separator = "`r`n"
        $payload = $utf8.GetBytes($separator + $hook)
        $stream = [System.IO.File]::Open($luaPath, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write)
        try {
            $stream.Write($payload, 0, $payload.Length)
        } finally {
            $stream.Close()
        }
    }
}

Write-Output "Installed 漢字通 into $rime"
Write-Output "Redeploy Weasel (重新部署) to compile the schema. This script does not deploy."
