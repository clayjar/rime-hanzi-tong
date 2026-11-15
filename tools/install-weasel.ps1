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

# Work line by line. A trailing CR would hide "patch:" from a $ anchor, and a
# second top-level patch: would replace the schema list.
$lines = New-Object System.Collections.Generic.List[string]
$skipRootOptions = $false
foreach ($line in [regex]::Split($customText, "\r\n|\n|\r")) {
    if (-not $skipRootOptions -and $line -match '^switcher/save_options/\+:\s*$') {
        $skipRootOptions = $true
        continue
    }
    if ($skipRootOptions) {
        if ($line -match '^\s*- disable_(guan|yue|min|han|ri)\s*$') {
            continue
        }
        $skipRootOptions = $false
    }
    $lines.Add($line)
}
while ($lines.Count -gt 0 -and $lines[$lines.Count - 1] -eq "") {
    $lines.RemoveAt($lines.Count - 1)
}

function Add-AfterFirstPatch {
    param(
        [System.Collections.Generic.List[string]]$Lines,
        [string[]]$Block
    )
    $index = -1
    for ($i = 0; $i -lt $Lines.Count; $i++) {
        if ($Lines[$i] -match '^patch:\s*$') {
            $index = $i
            break
        }
    }
    if ($index -lt 0) {
        if ($Lines.Count -gt 0) {
            $Lines.Add("")
        }
        $Lines.Add("patch:")
        $index = $Lines.Count - 1
    }
    for ($j = $Block.Count - 1; $j -ge 0; $j--) {
        $Lines.Insert($index + 1, $Block[$j])
    }
}

$hasSchema = $false
$hasSave = $false
foreach ($line in $lines) {
    if ($line -match 'schema:\s*hanzi_tong') { $hasSchema = $true }
    if ($line -match '^\s+switcher/save_options/\+:\s*$') { $hasSave = $true }
}
if (-not $hasSchema) {
    Add-AfterFirstPatch $lines @("  schema_list/+:", "    - schema: hanzi_tong")
}
# Omitting reset on a switch is not enough. Rime writes a menu choice to
# user.yaml only when the option name is listed in switcher/save_options.
if (-not $hasSave) {
    Add-AfterFirstPatch $lines @(
        "  switcher/save_options/+:",
        "    - disable_guan",
        "    - disable_yue",
        "    - disable_min",
        "    - disable_han",
        "    - disable_ri"
    )
}

# Drop a later patch: that only repeats the saved-option list.
$collapsed = New-Object System.Collections.Generic.List[string]
$seenPatch = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    if ($seenPatch -and $line -match '^patch:\s*$') {
        $next = if ($i + 1 -lt $lines.Count) { $lines[$i + 1] } else { "" }
        if ($next -match '^\s+switcher/save_options/\+:\s*$') {
            continue
        }
    }
    if ($line -match '^patch:\s*$') {
        $seenPatch = $true
    }
    $collapsed.Add($line)
}

$customText = ($collapsed -join "`r`n") + "`r`n"
[System.IO.File]::WriteAllText($custom, $customText, $utf8)

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
