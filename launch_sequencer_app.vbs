Option Explicit

Dim shell, fso, scriptDir, cmd, argText, i
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
argText = ""
For i = 0 To WScript.Arguments.Count - 1
  argText = argText & " " & Chr(34) & WScript.Arguments(i) & Chr(34)
Next
cmd = Chr(34) & scriptDir & "\launch_sequencer_app.cmd" & Chr(34) & argText

' Run hidden, do not wait.
shell.Run cmd, 0, False
