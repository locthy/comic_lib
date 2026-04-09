@echo off
:: Open Windows Terminal with a split pane
:: Left/Top pane: runs python server.py
:: Right/Bottom pane: runs python truyen.py

wt -p "Windows PowerShell" -d "%cd%" cmd /k "python server.py" ; split-pane -p "Windows PowerShell" -d "%cd%" cmd /k "python truyen.py"; -p "Windows PowerShell" -d "%cd%" cmd /k "python auto_update_comic.py"