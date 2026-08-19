@echo off
echo ============================================
echo  Bot de Noticias Facebook - %date% %time%
echo ============================================

cd /d "C:\Users\NERB\Desktop\Mi pagina de facebook"

echo Ejecutando bot...
python main.py >> "logs\output.log" 2>&1

echo Bot finalizado. Revisa logs\ para mas detalles.
