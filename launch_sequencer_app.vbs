Option Explicit

Dim shell, fso, scriptDir, cmd
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
cmd = Chr(34) & scriptDir & "\launch_sequencer_app.cmd" & Chr(34)

' Run hidden, do not wait.
shell.Run cmd, 0, False
