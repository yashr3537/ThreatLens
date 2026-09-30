
import flet as ft

from .scan_url import url_s_c




# ==================================================
# 1. URL VALIDATION FUNCTION
# ==================================================

def scan_url(url):

    # URL ke aage-peeche ki extra spaces hatao.
    # Agar url None ya empty hai, toh empty string use karo.
    url = (url or "").strip()

    # Check karo ki user ne URL enter kiya hai ya nahi.
    if not url:
        return "URL can't be empty"

    # Check karo ki URL http:// ya https:// se start hota hai.
    # Agar nahi hota, toh error message return karo.
    if not url.startswith(("http://", "https://")):
        return "Invalid URL format. Use http:// or https://"

    # Dono checks pass ho gaye toh URL ko valid format batao.
    return f"URL is valid: {url}"




# ==================================================
# 2. SINGLE URL INPUT PAGE BANANA
# ==================================================

def create_single_input_page():

    # User URL yahan enter karega.
    url_field = ft.TextField(
        label="Enter URL",
        hint_text="https://example.com",
        width=400,
    )

    # Scan ka result yahan show hoga.
    # Shuru mein result empty rahega.
    result_text = ft.Text(
        size=14,
        color="#AFC5D6"
    )
    url_display = ft.Container()

    # ==================================================
    # 3. SCAN BUTTON CLICK HONE PAR
    # ==================================================

    def on_scan(event):
        # User ki URL lo
        url = url_field.value

        # Pehle validation karo
        result = scan_url(url)

        # Result screen par dikhao
        result_text.value = result
        result_text.update()

        # Agar URL valid hai tab actual scanner ko bhejo
        if result.startswith("URL is valid:"):
            url_display.content = url_s_c(url)
            url_display.update()

    # ==================================================
    # 4. PAGE KA DESIGN RETURN KARNA
    # ==================================================

    return ft.Container(
        expand=True,  # Available jagah mein poora expand ho.

        # Page ke content ko center mein rakho.
        alignment=ft.Alignment.CENTER,

        # Page ke andar saare elements vertical order mein honge.
        content=ft.Column(
            [
                # Page ka heading.
                ft.Text(
                    "Single URL Scan",
                    size=24,
                    color="#00E5FF",
                    weight=ft.FontWeight.BOLD,
                ),

                # URL enter karne ka input field.
                url_field,

                # Button click karne par on_scan() chalega.
                ft.Button(
                    content="Scan URL",
                    on_click=on_scan,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor="#00E5FF",
                    ),
                ),

                # User ke liye instruction.
                ft.Text(
                    "Note: Please ensure the URL is valid "
                    "and starts with http:// or https://",
                    size=12,
                    color="#AFC5D6",
                ),

                # Validation ka result yahan dikhega.
                result_text,
                url_display,
            ],

            # Saare elements ko vertical direction mein center karo.
            alignment=ft.MainAxisAlignment.CENTER,

            # Elements ko horizontally center karo.
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )