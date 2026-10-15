
Add-Type @"
  using System;
  using System.Runtime.InteropServices;
  public class WinUtils {
    [DllImport("user32.dll")]
    public static extern bool EnumThreadWindows(int dwThreadId, EnumThreadDelegate lpfn, IntPtr lParam);
    public delegate bool EnumThreadDelegate(IntPtr hWnd, IntPtr lParam);
    [DllImport("user32.dll")]
    public static extern bool IsWindowVisible(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
    [DllImport("user32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern int GetClassName(IntPtr hWnd, System.Text.StringBuilder lpString, int nMaxCount);
  }
"@

$p = Get-Process -Name TaleSpire -ErrorAction SilentlyContinue
if ($p) {
    Write-Host "TaleSpire PID: $($p.Id)"
    foreach ($t in $p.Threads) {
        [WinUtils]::EnumThreadWindows($t.Id, [WinUtils+EnumThreadDelegate]{
            param($h, $l)
            $sbTitle = New-Object System.Text.StringBuilder 256
            [WinUtils]::GetWindowText($h, $sbTitle, 256) | Out-Null
            $sbClass = New-Object System.Text.StringBuilder 256
            [WinUtils]::GetClassName($h, $sbClass, 256) | Out-Null
            $vis = [WinUtils]::IsWindowVisible($h)
            Write-Host "Thread $($t.Id) Window: $h, Visible: $vis, Title: '$($sbTitle.ToString())', Class: '$($sbClass.ToString())'"
            return $true
        }, [IntPtr]::Zero) | Out-Null
    }
} else {
    Write-Host "TaleSpire not found"
}
