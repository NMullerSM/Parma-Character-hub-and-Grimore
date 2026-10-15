
Add-Type -Path 'C:\Program Files (x86)\Steam\steamapps\common\TaleSpire\TaleSpire_Data\Managed\UnityEngine.CoreModule.dll'
Add-Type -Path 'C:\Program Files (x86)\Steam\steamapps\common\TaleSpire\TaleSpire_Data\Managed\UnityEngine.UI.dll'

$asm = [System.Reflection.Assembly]::LoadFrom('C:\Program Files (x86)\Steam\steamapps\common\TaleSpire\TaleSpire_Data\Managed\Bouncyrock.TaleSpire.Runtime.dll')

try {
    $types = $asm.GetTypes()
} catch [System.Reflection.ReflectionTypeLoadException] {
    $types = $_.Exception.Types | Where-Object { $_ -ne $null }
}

Write-Host "=== Searching for Pipe or LCM in types ==="
$types | Where-Object { $_.Name -like '*Pipe*' -or $_.Name -like '*LCM*' -or $_.Name -like '*Uri*' } | ForEach-Object {
    Write-Host "$($_.FullName)"
}

Write-Host "`n=== Searching for Symbiote / Dice Results ==="
$types | Where-Object { $_.Name -like '*RollResult*' -or $_.Name -like '*DiceResult*' } | ForEach-Object {
    Write-Host "$($_.FullName)"
    $_.GetMethods([System.Reflection.BindingFlags]'Public,NonPublic,Instance,Static,DeclaredOnly') | ForEach-Object {
        Write-Host "   $($_.ReturnType.Name) $($_.Name)"
    }
}
