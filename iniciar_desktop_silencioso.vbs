Set WshShell = CreateObject("WScript.Shell")
strPath = WshShell.CurrentDirectory

' Inicia o servidor Python em segundo plano sem janela
WshShell.Run "python """ & strPath & "\server.py"" 4190", 0, False

WScript.Sleep 1500

' Abre o Microsoft Edge em modo janela de aplicativo nativo (PWA App Mode)
WshShell.Run "msedge.exe --app=http://localhost:4190 --window-size=1280,820", 1, False
