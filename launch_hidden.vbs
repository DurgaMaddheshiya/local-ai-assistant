
' launch_hidden.vbs
' Launches start_silent.bat completely hidden - no CMD window visible
Set objShell = CreateObject("WScript.Shell")
objShell.Run """" & CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName) & "\start_silent.bat""", 0, False
