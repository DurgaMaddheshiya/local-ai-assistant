' launch_hidden.vbs - Launches Durgara completely hidden
Dim objShell, strDir
Set objShell = CreateObject("WScript.Shell")
strDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
objShell.Run "cmd /c cd /d """ & strDir & """ && start_silent.bat", 0, False
Set objShell = Nothing
