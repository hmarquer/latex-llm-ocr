# LaTeX LLM OCR

Una herramienta de línea de comandos que convierte archivos PDF e imágenes a código LaTeX usando inteligencia artificial. Utiliza la API de OpenAI (a través de Azure AI) para procesar documentos y generar código LaTeX limpio y bien formateado.

## Características

- **Conversión de PDFs**: Extrae texto de archivos PDF y lo convierte a código LaTeX
- **PDFs escaneados**: Procesa PDFs que contienen solo imágenes (documentos escaneados) página por página con contexto acumulativo
- **Procesamiento de imágenes**: Convierte imágenes con contenido matemático/académico a LaTeX
- **Capturas de pantalla**: Toma capturas de región seleccionada y las procesa directamente
- **Modo TikZ**: Genera descripciones detalladas para recrear figuras matemáticas en TikZ
- **Multiplataforma**: Compatible con Linux, macOS y Windows
- **Portapapeles automático**: Copia automáticamente el resultado al portapapeles
- **Notificaciones**: Envía notificaciones del sistema al completar el procesamiento

## Requisitos del Sistema

### Dependencias de Python
- Python 3.7+
- openai
- PyPDF2
- pdf2image

### Herramientas del Sistema (Opcionales)

#### Linux
Para capturas de pantalla (al menos una):
- `shutter` (recomendado)
- `gnome-screenshot`
- `spectacle`
- `scrot`

Para conversión de PDFs a imágenes:
- `poppler-utils`: `sudo apt install poppler-utils`

Para portapapeles:
- `xclip` (recomendado): `sudo apt install xclip`
- `xsel`: `sudo apt install xsel`

Para notificaciones:
- `notify-send` (usualmente incluido)

#### macOS
- `screencapture` (incluido en el sistema)
- `pbcopy` (incluido en el sistema)
- `osascript` (incluido en el sistema)
- `poppler` para PDFs: `brew install poppler`

#### Windows
- PowerShell (incluido en Windows 10+)
- `clip` (incluido en el sistema)

## Instalación

### 1. Clonar el repositorio
```bash
git clone https://github.com/hmarquer/latex-llm-ocr.git
cd latex-llm-ocr
```

### 2. Crear y activar entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate  # En Linux/macOS
# o
.venv\Scripts\activate     # En Windows
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variable de entorno
El script requiere una API key configurada como variable de entorno `GITHUB_API_KEY`:

```bash
export GITHUB_API_KEY="tu_api_key_aqui"
```

Para hacerlo permanente, agrégalo a tu archivo `~/.bashrc` o `~/.zshrc`:
```bash
echo 'export GITHUB_API_KEY="tu_api_key_aqui"' >> ~/.bashrc
source ~/.bashrc
```

## Uso

### Sintaxis básica
```bash
python latex-llm-ocr.py [archivo] [opciones]
```

### Ejemplos de uso

#### 1. Convertir un archivo PDF
```bash
python latex-llm-ocr.py documento.pdf
```

#### 2. Convertir una imagen
```bash
python latex-llm-ocr.py imagen.png
```

#### 3. Tomar captura de pantalla y convertir
```bash
python latex-llm-ocr.py --screenshot
# o
python latex-llm-ocr.py -s
```

#### 4. Generar descripción TikZ de una imagen
```bash
python latex-llm-ocr.py imagen.png --tikz
# o
python latex-llm-ocr.py imagen.png -t
```

#### 5. Captura de pantalla con descripción TikZ
```bash
python latex-llm-ocr.py --screenshot --tikz
```

#### 6. Procesar PDF escaneado (solo imágenes)
```bash
python latex-llm-ocr.py documento_escaneado.pdf --pdf-as-images
```

#### 7. PDF escaneado con descripciones TikZ
```bash
python latex-llm-ocr.py figuras_matematicas.pdf --pdf-as-images --tikz
```

### Opciones disponibles

| Opción | Descripción |
|--------|-------------|
| `-s, --screenshot` | Toma una captura de pantalla de región seleccionada |
| `-t, --tikz` | Genera descripción detallada para recrear figuras en TikZ |
| `-p, --pdf-as-images` | Procesa PDF como imágenes escaneadas (página por página con contexto) |
| `-h, --help` | Muestra la ayuda completa |

## Formatos soportados

### Imágenes
- `.png`
- `.jpg`
- `.jpeg`
- `.gif`
- `.bmp`
- `.webp`

### Documentos
- `.pdf`

### Limitaciones
- Tamaño máximo de archivo: 20 MB
- Los archivos PDF se procesan extrayendo el texto por defecto
- Para PDFs escaneados (solo imágenes), usar la opción `--pdf-as-images`
- El procesamiento de PDFs como imágenes puede ser más lento debido al procesamiento secuencial

## Funcionalidades del código LaTeX generado

El código LaTeX generado sigue estas convenciones:

- **Matemáticas inline**: `$ ... $`
- **Matemáticas display**: `\\[ ... \\]`
- **Ecuaciones multilínea**: `align` environment
- **Funciones por partes**: `cases` environment
- **Listas numeradas**: `enumerate` environment
- **Listas no numeradas**: `itemize` environment

### Entornos matemáticos personalizados
- `ejem` - Ejemplos
- `teo` - Teoremas
- `prop` - Proposiciones
- `cor` - Corolarios
- `lem` - Lemas
- `defn` - Definiciones
- `obs` - Observaciones
- `sol` - Soluciones
- `dem` - Demostraciones

### Símbolos especiales
- `\\R, \\Q, \\C, \\Z, \\N` - Conjuntos numéricos
- `\\abs{}` - Valor absoluto
- `\\norm{}` - Norma
- `\\ind_{}` - Función indicadora
- `\\implies, \\impliedby` - Implicaciones

### Personalización de prompts
Los prompts se pueden modificar en `prompts.py`:
- `STANDARD_INSTRUCTIONS` - Reglas de formato LaTeX
- `SYSTEM_PROMPTS` - Prompts del sistema para diferentes modos

### Configuración del modelo
En `latex-llm-ocr.py`, línea ~376:
```python
model = "gpt-4o"
temperature = 0.05
max_tokens = 4090
```

## Arquitectura del código

```
latex-llm-ocr.py          # Script principal
├── load_openai_client()  # Configuración de API
├── validate_file()       # Validación de archivos
├── take_screenshot()     # Captura multiplataforma
├── copy_to_clipboard()   # Portapapeles multiplataforma
├── send_notification()   # Notificaciones del sistema
├── encode_image()        # Codificación base64
├── extract_pdf_text()    # Extracción de texto PDF
├── convert_pdf_to_images() # Conversión PDF a imágenes
├── process_pdf_as_images() # Procesamiento secuencial con contexto
└── process_file()        # Procesamiento con IA

prompts.py                # Módulo de prompts
├── STANDARD_INSTRUCTIONS # Reglas de formato LaTeX
├── SYSTEM_PROMPTS        # Prompts del sistema
├── messages_image()      # Prompts para imágenes
├── messages_text()       # Prompts para texto PDF
├── messages_tikz_describer() # Prompts para TikZ
├── messages_pdf_image_first_page() # Primera página PDF escaneado
└── messages_pdf_image_with_context() # Páginas subsecuentes con contexto
```

## Nota sobre costos

Este script utiliza la API de OpenAI/Azure AI que puede tener costos asociados. Revisa los precios en la documentación oficial antes de usar extensivamente.