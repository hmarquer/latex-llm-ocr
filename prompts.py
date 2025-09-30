"""
Módulo para generar prompts para la conversión de documentos a LaTeX.
Contiene las instrucciones estándar y funciones para crear mensajes específicos.
"""

from typing import List, Dict, Any

# Instrucciones estándar para la generación de código LaTeX
STANDARD_INSTRUCTIONS = """
The result must satisfy these requirements:
-- Only write the code, skip any comments or explanations and do not include the usual ```latex ... ```, just the raw code.
-- Do not include a preamble.
-- Use $ ... $ for inline math and \\[ ... \\] for display math.
-- Use \\begin{<env>} ... \\end{<env>} for different environments where <env> is replaced by:
   • 'ejem' for examples
   • 'teo' for theorems  
   • 'prop' for propositions
   • 'cor' for corollaries
   • 'lem' for lemmas
   • 'defn' for definitions
   • 'obs' for observations
   • 'sol' for solutions
   • 'dem' for demonstrations
   ONLY if any are present.
-- Use the 'enumerate' environment for lists (e.g. lists of exercises) and the 'itemize' environment for unordered lists. NEVER specify the item type.
-- Use the 'align' environment for multiline equations.
-- Use the 'cases' environment for piecewise functions.
-- Use \\ind_{} for the indicator function.
-- Use \\abs{} for absolute values.
-- Use \\norm{} for norms.
-- Use \\R, \\Q, \\C, \\Z, \\N for the real, rational, complex, integer and natural numbers, respectively.
-- Use \\implies for the implication symbol and \\impliedby for the reverse implication symbol.
"""

# Prompts del sistema para diferentes tipos de conversión
SYSTEM_PROMPTS = {
    "latex_generator": "You are a helpful AI assistant trained in LaTeX document generation. You excel at converting various content types into proper LaTeX code following specific formatting requirements.",
    "tikz_describer": "You are a helpful AI assistant trained in mathematical diagram interpretation. You specialize in analyzing mathematical figures and providing detailed descriptions for TikZ recreation.",
}

def messages_image(base64_image: str) -> List[Dict[str, Any]]:
    """
    Genera mensajes para convertir una imagen a código LaTeX.
    
    Args:
        base64_image: Imagen codificada en base64
        
    Returns:
        Lista de mensajes para la API de OpenAI
    """
    if not base64_image:
        raise ValueError("base64_image no puede estar vacío")
    
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS["latex_generator"],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"Write the LaTeX code for the following image. {STANDARD_INSTRUCTIONS}",
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            ]
        }
    ]

def messages_text(text: str) -> List[Dict[str, Any]]:
    """
    Genera mensajes para convertir texto extraído de PDF a código LaTeX.
    
    Args:
        text: Texto extraído del PDF
        
    Returns:
        Lista de mensajes para la API de OpenAI
    """
    if not text or not text.strip():
        raise ValueError("El texto no puede estar vacío")
    
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS["latex_generator"],
        },
        {
            "role": "user",
            "content": (
                f"Write the LaTeX code for the following text that has been extracted from a PDF file. "
                f"{STANDARD_INSTRUCTIONS}\n\n"
                f"The text is as follows:\n{text}"
            ),
        }
    ]

def messages_tikz_describer(base64_image: str) -> List[Dict[str, Any]]:
    """
    Genera mensajes para describir una figura matemática y proporcionar instrucciones TikZ.
    
    Args:
        base64_image: Imagen codificada en base64
        
    Returns:
        Lista de mensajes para la API de OpenAI
    """
    if not base64_image:
        raise ValueError("base64_image no puede estar vacío")
    
    tikz_instructions = """
    Describe in great detail the following mathematical figure. What is it about? What is it trying to show? 
    What are the main components and how are they related and positioned?

    After that description, include a comprehensive list of instructions to draw the figure in TikZ. 
    The instructions should be as detailed as possible and should include:
    
    • The main components of the figure and their mathematical significance
    • The colors of the components (be specific about color names)
    • The exact positions and coordinates of the components
    • The relationships and connections between components
    • Line styles, arrow types, and other visual elements
    • Text labels, mathematical expressions, and their positioning
    • Scale and proportions of different elements
    • Any geometric transformations or special arrangements
    • Suggested TikZ libraries that might be needed
    • Any other relevant information that can help recreate the figure accurately in TikZ
    
    Organize the instructions in a logical order for implementation.
    """
    
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS["tikz_describer"],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": tikz_instructions,
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            ]
        }
    ]

def messages_pdf_image_first_page(base64_image: str) -> List[Dict[str, Any]]:
    """
    Genera mensajes para convertir la primera página de un PDF escaneado a código LaTeX.
    
    Args:
        base64_image: Imagen de la primera página codificada en base64
        
    Returns:
        Lista de mensajes para la API de OpenAI
    """
    if not base64_image:
        raise ValueError("base64_image no puede estar vacío")
    
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS["latex_generator"],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"This is the first page of a scanned PDF document. "
                        f"Write the LaTeX code for this page. This page will be followed by more pages, "
                        f"so ensure the content flows naturally and can be continued. "
                        f"{STANDARD_INSTRUCTIONS}"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            ]
        }
    ]

def messages_pdf_image_with_context(base64_image: str, previous_latex: str) -> List[Dict[str, Any]]:
    """
    Genera mensajes para convertir una página subsecuente de un PDF escaneado con contexto.
    
    Args:
        base64_image: Imagen de la página actual codificada in base64
        previous_latex: Código LaTeX de las páginas anteriores
        
    Returns:
        Lista de mensajes para la API de OpenAI
    """
    if not base64_image:
        raise ValueError("base64_image no puede estar vacío")
    
    if not previous_latex or not previous_latex.strip():
        raise ValueError("previous_latex no puede estar vacío")
    
    # Truncar el contexto si es demasiado largo para evitar límites de tokens
    max_context_length = 2000
    if len(previous_latex) > max_context_length:
        # Tomar los últimos caracteres para mantener el contexto más reciente
        previous_latex = "..." + previous_latex[-max_context_length:]
    
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPTS["latex_generator"],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"This is a continuation page from a scanned PDF document. "
                        f"Below is the LaTeX code from the previous pages:\n\n"
                        f"--- PREVIOUS PAGES CONTEXT ---\n"
                        f"{previous_latex}\n"
                        f"--- END CONTEXT ---\n\n"
                        f"Now write the LaTeX code for this new page, ensuring it continues "
                        f"naturally from the previous content. Maintain consistency in notation, "
                        f"formatting, and mathematical style. Only provide the LaTeX code for THIS page. "
                        f"{STANDARD_INSTRUCTIONS}"
                    ),
                },
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                }
            ]
        }
    ]

# Funciones auxiliares para personalización futura
def get_custom_latex_instructions(additional_rules: List[str] = None) -> str:
    """
    Permite agregar reglas adicionales a las instrucciones estándar.
    
    Args:
        additional_rules: Lista de reglas adicionales a agregar
        
    Returns:
        Instrucciones personalizadas
    """
    instructions = STANDARD_INSTRUCTIONS
    
    if additional_rules:
        additional_text = "\n".join(f"-- {rule}" for rule in additional_rules)
        instructions += f"\n{additional_text}"
    
    return instructions

def validate_base64_image(base64_image: str) -> bool:
    """
    Valida que el string de base64 sea válido.
    
    Args:
        base64_image: String a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    try:
        import base64
        base64.b64decode(base64_image, validate=True)
        return True
    except Exception:
        return False