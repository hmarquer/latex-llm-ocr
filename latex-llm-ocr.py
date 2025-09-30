import os
import sys
import base64
from pathlib import Path
from typing import Optional, List
from openai import OpenAI
import prompts
import argparse
import PyPDF2
import subprocess
import tempfile
import time
import platform
from pdf2image import convert_from_path

# Configuración
SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
SUPPORTED_EXTENSIONS = {'.pdf'} | SUPPORTED_IMAGE_EXTENSIONS
MAX_FILE_SIZE_MB = 20  # Límite de tamaño de archivo en MB

def load_openai_client() -> OpenAI:
    """Carga el cliente de OpenAI con validación de API key."""
    # _ = load_dotenv(find_dotenv())
    api_key = os.environ.get('GITHUB_API_KEY')
    
    if not api_key:
        print("Error: OPENAI_API_KEY no encontrada en las variables de entorno.", file=sys.stderr)
        sys.exit(1)
    
    return OpenAI(
        base_url="https://models.inference.ai.azure.com",
        api_key=api_key,
    )

def validate_file(filepath: str) -> Path:
    """Valida que el archivo existe y tiene una extensión soportada."""
    file_path = Path(filepath)
    
    if not file_path.exists():
        print(f"Error: El archivo '{filepath}' no existe.", file=sys.stderr)
        sys.exit(1)
    
    if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        print(f"Error: Extensión '{file_path.suffix}' no soportada. "
              f"Extensiones válidas: {', '.join(SUPPORTED_EXTENSIONS)}", file=sys.stderr)
        sys.exit(1)
    
    # Verificar tamaño del archivo
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > MAX_FILE_SIZE_MB:
        print(f"Error: El archivo es demasiado grande ({file_size_mb:.1f}MB). "
              f"Máximo permitido: {MAX_FILE_SIZE_MB}MB", file=sys.stderr)
        sys.exit(1)
    
    return file_path

def take_screenshot() -> Path:
    """Toma una captura de pantalla de una región seleccionada de manera multiplataforma."""
    system = platform.system().lower()
    
    try:
        # Crear archivo temporal para la captura
        temp_dir = Path(tempfile.gettempdir())
        timestamp = int(time.time())
        screenshot_path = temp_dir / f"latex_ocr_screenshot_{timestamp}.png"
        
        if system == 'linux':
            # Linux: Probar diferentes herramientas de captura
            tools = [
                (['shutter', '-s', '-e', '-n', '-o', str(screenshot_path)], 'shutter'),
                (['gnome-screenshot', '-a', '-f', str(screenshot_path)], 'gnome-screenshot'),
                (['spectacle', '-r', '-b', '-n', '-o', str(screenshot_path)], 'spectacle'),
                (['scrot', '-s', str(screenshot_path)], 'scrot')
            ]
            
            success = False
            for cmd, tool_name in tools:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    if result.returncode == 0 and screenshot_path.exists():
                        success = True
                        break
                except FileNotFoundError:
                    continue
            
            if not success:
                print("Error: No se encontró herramienta de captura. Instala una de: shutter, gnome-screenshot, spectacle, scrot", file=sys.stderr)
                sys.exit(1)
                
        elif system == 'darwin':  # macOS
            result = subprocess.run([
                'screencapture', '-i', '-s', str(screenshot_path)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error al tomar captura de pantalla: {result.stderr}", file=sys.stderr)
                sys.exit(1)
                
        elif system == 'windows':
            # Windows: Usar PowerShell con Add-Type para captura interactiva
            ps_script = f'''
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            
            $form = New-Object Windows.Forms.Form
            $form.WindowState = "Maximized"
            $form.BackColor = "Black"
            $form.Opacity = 0.3
            $form.TopMost = $true
            $form.FormBorderStyle = "None"
            $form.Cursor = [System.Windows.Forms.Cursors]::Cross
            
            $startPoint = New-Object System.Drawing.Point
            $endPoint = New-Object System.Drawing.Point
            $isSelecting = $false
            
            $form.add_MouseDown({{ 
                $script:startPoint = $_.Location
                $script:isSelecting = $true
            }})
            
            $form.add_MouseUp({{
                $script:endPoint = $_.Location
                $form.Close()
            }})
            
            $form.ShowDialog() | Out-Null
            
            if ($isSelecting) {{
                $width = [Math]::Abs($endPoint.X - $startPoint.X)
                $height = [Math]::Abs($endPoint.Y - $startPoint.Y)
                $x = [Math]::Min($startPoint.X, $endPoint.X)
                $y = [Math]::Min($startPoint.Y, $endPoint.Y)
                
                $bitmap = New-Object System.Drawing.Bitmap($width, $height)
                $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
                $graphics.CopyFromScreen($x, $y, 0, 0, $bitmap.Size)
                $bitmap.Save("{screenshot_path}", [System.Drawing.Imaging.ImageFormat]::Png)
                $graphics.Dispose()
                $bitmap.Dispose()
            }}
            '''
            
            result = subprocess.run([
                'powershell', '-Command', ps_script
            ], capture_output=True, text=True, shell=True)
            
            if result.returncode != 0:
                print(f"Error al tomar captura de pantalla: {result.stderr}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"Error: Sistema operativo '{system}' no soportado para capturas de pantalla.", file=sys.stderr)
            sys.exit(1)
        
        if not screenshot_path.exists():
            print("Error: No se pudo crear el archivo de captura de pantalla.", file=sys.stderr)
            sys.exit(1)
        
        return screenshot_path
    
    except Exception as e:
        print(f"Error inesperado al tomar captura: {e}", file=sys.stderr)
        sys.exit(1)

def copy_to_clipboard(text: str) -> None:
    """Copia el texto al portapapeles de manera multiplataforma."""
    system = platform.system().lower()
    
    try:
        if system == 'linux':
            # Linux: usar xclip o xsel
            try:
                process = subprocess.Popen(
                    ['xclip', '-selection', 'clipboard'],
                    stdin=subprocess.PIPE,
                    text=True
                )
                process.communicate(input=text)
                success = process.returncode == 0
            except FileNotFoundError:
                try:
                    process = subprocess.Popen(
                        ['xsel', '--clipboard', '--input'],
                        stdin=subprocess.PIPE,
                        text=True
                    )
                    process.communicate(input=text)
                    success = process.returncode == 0
                except FileNotFoundError:
                    print("Advertencia: Instala 'xclip' o 'xsel' para el portapapeles: sudo apt install xclip", file=sys.stderr)
                    success = False
                    
        elif system == 'darwin':  # macOS
            process = subprocess.Popen(
                ['pbcopy'],
                stdin=subprocess.PIPE,
                text=True
            )
            process.communicate(input=text)
            success = process.returncode == 0
            
        elif system == 'windows':
            process = subprocess.Popen(
                ['clip'],
                stdin=subprocess.PIPE,
                text=True,
                shell=True
            )
            process.communicate(input=text)
            success = process.returncode == 0
        else:
            print(f"Advertencia: Sistema operativo '{system}' no soportado para portapapeles.", file=sys.stderr)
            success = False
        
        if success:
            print("✓ Resultado copiado al portapapeles.", file=sys.stderr)
            send_notification("LaTeX OCR completado", "Texto copiado al portapapeles.")
        else:
            print("Advertencia: No se pudo copiar al portapapeles.", file=sys.stderr)
            
    except Exception as e:
        print(f"Advertencia: Error al copiar al portapapeles: {e}", file=sys.stderr)

def send_notification(title: str, message: str) -> None:
    """Envía una notificación al usuario de manera multiplataforma."""
    system = platform.system().lower()
    
    try:
        if system == 'linux':
            subprocess.run([
                'notify-send', title, message
            ], check=False, capture_output=True)
        elif system == 'darwin':  # macOS
            subprocess.run([
                'osascript', '-e',
                f'display notification "{message}" with title "{title}"'
            ], check=False, capture_output=True)
        elif system == 'windows':
            # Usar PowerShell para notificaciones en Windows 10+
            ps_command = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $toastXml = [xml] $template.GetXml()
            $toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("{title}")) > $null
            $toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("{message}")) > $null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($toastXml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("LaTeX OCR").Show($toast)
            '''
            subprocess.run([
                'powershell', '-Command', ps_command
            ], check=False, capture_output=True, shell=True)
    except Exception:
        # Ignorar errores de notificación silenciosamente
        pass

def encode_image(image_path: Path) -> str:
    """Codifica una imagen a base64."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except IOError as e:
        print(f"Error al leer la imagen: {e}", file=sys.stderr)
        sys.exit(1)

def extract_pdf_text(pdf_path: Path) -> str:
    """Extrae texto de un archivo PDF."""
    try:
        contents = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                contents += page.extract_text()
        
        if not contents.strip():
            print("Advertencia: No se pudo extraer texto del PDF.", file=sys.stderr)
        
        return contents
    except Exception as e:
        print(f"Error al procesar el PDF: {e}", file=sys.stderr)
        sys.exit(1)

def convert_pdf_to_images(pdf_path: Path) -> List[Path]:
    """Convierte un PDF a una lista de imágenes temporales."""
    try:
        print(f"Convirtiendo PDF a imágenes...", file=sys.stderr)
        
        # Crear directorio temporal para las imágenes
        temp_dir = Path(tempfile.mkdtemp(prefix="latex_ocr_pdf_"))
        
        # Convertir PDF a imágenes
        images = convert_from_path(pdf_path, dpi=300, fmt='PNG')
        
        image_paths = []
        for i, image in enumerate(images, 1):
            image_path = temp_dir / f"page_{i:03d}.png"
            image.save(image_path, 'PNG')
            image_paths.append(image_path)
        
        print(f"✓ PDF convertido a {len(image_paths)} imágenes.", file=sys.stderr)
        return image_paths
        
    except Exception as e:
        print(f"Error al convertir PDF a imágenes: {e}", file=sys.stderr)
        print("Nota: Asegúrate de tener poppler-utils instalado:", file=sys.stderr)
        print("  Ubuntu/Debian: sudo apt install poppler-utils", file=sys.stderr)
        print("  macOS: brew install poppler", file=sys.stderr)
        print("  Windows: Consulta la documentación de pdf2image", file=sys.stderr)
        sys.exit(1)

def process_pdf_as_images(client: OpenAI, pdf_path: Path, use_tikz: bool = False) -> str:
    """Procesa un PDF como imágenes secuencialmente con contexto acumulativo."""
    model = "gpt-4o"
    temperature = 0.05
    max_tokens = 4090
    
    try:
        # Convertir PDF a imágenes
        image_paths = convert_pdf_to_images(pdf_path)
        
        accumulated_latex = ""
        total_pages = len(image_paths)
        
        for i, image_path in enumerate(image_paths, 1):
            print(f"Procesando página {i}/{total_pages}...", file=sys.stderr)
            
            base64_image = encode_image(image_path)
            
            if i == 1:
                # Primera página: sin contexto
                if use_tikz:
                    messages = prompts.messages_tikz_describer(base64_image)
                else:
                    messages = prompts.messages_pdf_image_first_page(base64_image)
            else:
                # Páginas siguientes: con contexto de páginas anteriores
                if use_tikz:
                    messages = prompts.messages_tikz_describer(base64_image)
                else:
                    messages = prompts.messages_pdf_image_with_context(base64_image, accumulated_latex)
            
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=1
            )
            
            page_latex = response.choices[0].message.content
            
            if i == 1:
                accumulated_latex = page_latex
            else:
                # Agregar nueva página al contenido acumulado
                accumulated_latex += "\n\n" + page_latex
            
            print(f"✓ Página {i} procesada.", file=sys.stderr)
        
        # Limpiar archivos temporales
        for image_path in image_paths:
            try:
                image_path.unlink()
            except:
                pass
        
        # Limpiar directorio temporal
        try:
            image_paths[0].parent.rmdir()
        except:
            pass
        
        return accumulated_latex
        
    except Exception as e:
        print(f"Error al procesar PDF como imágenes: {e}", file=sys.stderr)
        sys.exit(1)

def process_file(client: OpenAI, file_path: Path, use_tikz: bool = False, pdf_as_images: bool = False) -> str:
    """Procesa un archivo y retorna la respuesta de OpenAI."""
    model = "gpt-4o"
    temperature = 0.05
    max_tokens = 4090
    
    try:
        if file_path.suffix.lower() == '.pdf':
            if pdf_as_images:
                return process_pdf_as_images(client, file_path, use_tikz)
            else:
                contents = extract_pdf_text(file_path)
                messages = prompts.messages_text(contents)
        else:
            base64_image = encode_image(file_path)
            if use_tikz:
                messages = prompts.messages_tikz_describer(base64_image)
            else:
                messages = prompts.messages_image(base64_image)

        response = client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"Error al procesar con OpenAI: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Función principal del script."""
    parser = argparse.ArgumentParser(
        description='Convierte archivos PDF e imágenes a código LaTeX usando IA',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Extensiones soportadas:
  PDF: .pdf (texto o imágenes escaneadas)
  Imágenes: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}

Ejemplos:
  %(prog)s document.pdf
  %(prog)s document.pdf --pdf-as-images
  %(prog)s image.png --tikz
  %(prog)s --screenshot
  %(prog)s --screenshot --tikz
        """
    )
    parser.add_argument('filepath', type=str, nargs='?', help='Ruta al archivo a convertir')
    parser.add_argument('-s', '--screenshot', action='store_true',
                       help='Tomar captura de pantalla de una región')
    parser.add_argument('-t', '--tikz', action='store_true', 
                       help='Usar descripción TikZ para imágenes')
    parser.add_argument('-p', '--pdf-as-images', action='store_true',
                       help='Procesar PDF como imágenes escaneadas (página por página con contexto)')
    
    args = parser.parse_args()
    
    # Validar argumentos
    if args.screenshot and args.filepath:
        parser.error("No se puede usar --screenshot junto con un archivo específico")
    elif not args.screenshot and not args.filepath:
        parser.error("Debe proporcionar un archivo o usar --screenshot")
    
    if args.pdf_as_images and args.screenshot:
        parser.error("No se puede usar --pdf-as-images con --screenshot")
    
    if args.pdf_as_images and args.filepath and not args.filepath.lower().endswith('.pdf'):
        parser.error("--pdf-as-images solo se puede usar con archivos PDF")
    
    # Cargar cliente OpenAI
    client = load_openai_client()
    
    try:
        if args.screenshot:
            # Tomar captura de pantalla
            file_path = take_screenshot()
            print(f"Captura guardada en: {file_path}", file=sys.stderr)
        else:
            # Validar archivo proporcionado
            file_path = validate_file(args.filepath)
        
        # Procesar archivo
        result = process_file(client, file_path, args.tikz, args.pdf_as_images)
        
        # Mostrar resultado
        print(result)
        
        # Copiar al portapapeles
        copy_to_clipboard(result)
        
    finally:
        # Limpiar archivo temporal si se usó screenshot
        if args.screenshot and 'file_path' in locals():
            try:
                file_path.unlink()
            except:
                pass

if __name__ == "__main__":
    main()
