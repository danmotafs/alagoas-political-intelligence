@echo off

echo ========================================
echo GERANDO ARQUITETURA DO PROJETO
echo ========================================

echo. > arquitetura_projeto.txt
echo ======================================== >> arquitetura_projeto.txt
echo ARQUITETURA DO PROJETO >> arquitetura_projeto.txt
echo ======================================== >> arquitetura_projeto.txt
echo. >> arquitetura_projeto.txt

echo ===== ESTRUTURA DE PASTAS ===== >> arquitetura_projeto.txt
tree /a >> arquitetura_projeto.txt

echo. >> arquitetura_projeto.txt
echo ===== INVENTARIO COMPLETO ===== >> arquitetura_projeto.txt
echo. >> arquitetura_projeto.txt

dir /s /b >> arquitetura_projeto.txt

echo.
echo Arquivo gerado:
echo %cd%\arquitetura_projeto.txt
echo.

pause