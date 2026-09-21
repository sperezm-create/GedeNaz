# GedeNaz App - Cliente Android en Python

Este directorio contiene una primera base de app movil usando Python + Kivy.
La API Flask vive en `../src/gedenaz/`.

## Donde escribir los comandos

Los comandos se escriben en la terminal de VS Code:

1. Abre VS Code en la carpeta `GedeNaz-main`.
2. Menu superior: `Terminal` > `New Terminal`.
3. Confirma que la terminal este parada en la raiz del proyecto.

Si no estas en la raiz, ejecuta:

```powershell
cd "C:\Users\Infinite\Desktop\Programas\gedenaz\GedeNaz-main"
```

## Probar la ventana en Windows

Primero activa el entorno virtual del backend, que ya existe en la raiz:

```powershell
.\venv\Scripts\Activate.ps1
```

Instala Kivy para la app movil:

```powershell
python -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r mobile\kivy_app\requirements.txt
```

Ejecuta la ventana:

```powershell
python mobile\kivy_app\main.py
```

La app usa por defecto la API local:

```text
http://127.0.0.1:5000
```

Si quieres usar otra URL:

```powershell
$env:GEDENAZ_API_URL="https://gedenaz-api.onrender.com"
python mobile\kivy_app\main.py
```

## Probar con Android

Para Android se recomienda este flujo:

1. Instalar Android Studio.
2. Abrir `Device Manager` y crear un emulador Android.
3. Usar Buildozer desde Linux/WSL para generar el APK.
4. Instalar el APK en el emulador de Android Studio.

En Windows, Buildozer no trabaja bien de forma nativa. Lo normal es usar WSL:

```powershell
wsl --install -d Ubuntu
```

Luego, dentro de Ubuntu/WSL:

```bash
cd "/mnt/c/Users/Infinite/Desktop/Programas/gedenaz/GedeNaz-main/mobile/kivy_app"
python3 -m pip install --user buildozer
buildozer android debug
```

El APK quedara en:

```text
mobile/kivy_app/bin/
```

Para instalarlo en un emulador abierto:

```bash
buildozer android deploy run
```

## Nota de red para emulador

Si la API Flask corre en tu PC y la app corre dentro del emulador Android,
`127.0.0.1` ya no apunta a tu PC, apunta al emulador. En Android Emulator se
usa:

```text
http://10.0.2.2:5000
```

Para el APK, hay que dejar esa URL configurada antes de compilar o moverla a
un archivo de configuracion mas adelante.
