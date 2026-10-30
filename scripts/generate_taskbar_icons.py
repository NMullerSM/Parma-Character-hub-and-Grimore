"""
Generador de Iconos de Barra de Tareas de Alta Visibilidad para Parma.
Renderiza el escudo sólido vectorial (en variantes clara y oscura)
y produce iconos .ico multi-resolución (16x16 a 256x256) y PNGs cuadrados
para evitar que el logo se pierda o se vea diminuto en Windows y Linux.
"""
import os
import sys

try:
    import fitz  # PyMuPDF
    from PIL import Image
except ImportError:
    print("[Error] Se requieren 'pymupdf' y 'pillow'. Ejecuta: pip install pymupdf pillow")
    sys.exit(1)


def render_svg_to_image(svg_path: str, size: int) -> Image.Image:
    """Renderiza un SVG a Pillow Image con fondo transparente y anti-aliasing perfecto."""
    with open(svg_path, "rb") as f:
        svg_bytes = f.read()

    doc = fitz.open(stream=svg_bytes, filetype="svg")
    page = doc[0]
    # Calcular escala necesaria
    scale = size / max(page.rect.width, page.rect.height)
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=True)
    mode = "RGBA" if pix.alpha else "RGB"
    img = Image.frombytes(mode, [pix.width, pix.height], pix.samples)
    doc.close()

    # Si hay una ligera discrepancia de tamaño, ajustar a lienzo cuadrado centrado
    if img.size != (size, size):
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        offset_x = (size - img.width) // 2
        offset_y = (size - img.height) // 2
        canvas.paste(img, (offset_x, offset_y), img)
        return canvas
    return img


def generate_icons():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dark_svg = os.path.join(base_dir, "brand", "es", "icon-shield-solid-dark.svg")
    light_svg = os.path.join(base_dir, "brand", "es", "icon-shield-solid-light.svg")

    if not os.path.exists(dark_svg) or not os.path.exists(light_svg):
        print(f"[Error] Archivos SVG fuente no encontrados en {dark_svg} o {light_svg}")
        return

    sizes = [16, 24, 32, 48, 64, 128, 256]

    print("[Iconos Parma] Renderizando capas vectoriales multi-resolución...")

    # 1. Variante Oscura (Escudo Negro Sólido para Barras de Tareas Claras)
    dark_images = [render_svg_to_image(dark_svg, s) for s in sizes]
    dark_ico_path = os.path.join(base_dir, "parma_taskbar_dark.ico")
    dark_png_path = os.path.join(base_dir, "parma_taskbar_dark.png")
    dark_images[-1].save(dark_ico_path, format="ICO", sizes=[(s, s) for s in sizes], append_images=dark_images[:-1])
    dark_images[-1].save(dark_png_path, format="PNG")
    print(f" -> Generado: {os.path.basename(dark_ico_path)} y {os.path.basename(dark_png_path)}")

    # 2. Variante Clara (Escudo Blanco Sólido para Barras de Tareas Oscuras)
    light_images = [render_svg_to_image(light_svg, s) for s in sizes]
    light_ico_path = os.path.join(base_dir, "parma_taskbar_light.ico")
    light_png_path = os.path.join(base_dir, "parma_taskbar_light.png")
    light_images[-1].save(light_ico_path, format="ICO", sizes=[(s, s) for s in sizes], append_images=light_images[:-1])
    light_images[-1].save(light_png_path, format="PNG")
    print(f" -> Generado: {os.path.basename(light_ico_path)} y {os.path.basename(light_png_path)}")

    # 3. Master parma.ico y parma.png (Sustituyen los iconos antiguos difusos)
    master_ico = os.path.join(base_dir, "parma.ico")
    master_png = os.path.join(base_dir, "parma.png")
    light_images[-1].save(master_ico, format="ICO", sizes=[(s, s) for s in sizes], append_images=light_images[:-1])
    light_images[-1].save(master_png, format="PNG")
    print(f" -> Actualizado master: {os.path.basename(master_ico)} y {os.path.basename(master_png)}")

    # 4. Actualizar favicon en frontend/public
    fav_ico = os.path.join(base_dir, "frontend", "public", "favicon.ico")
    if os.path.exists(os.path.dirname(fav_ico)):
        light_images[-1].save(fav_ico, format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
        print(f" -> Actualizado: {fav_ico}")

    print("[Iconos Parma] ¡Proceso completado con éxito!")


if __name__ == "__main__":
    generate_icons()
