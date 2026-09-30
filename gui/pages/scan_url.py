import flet as ft
import subprocess
import json


def url_s_c(url):

    # URL ke aage-peeche ki extra spaces hata rahe hain.
    url = (url or "").strip()

    # Agar URL empty hai to wahi par error dikha do.
    if not url:
        return ft.Container(
            content=ft.Text(
                "URL can't be empty",
                size=14,
                color="#AFC5D6",
            )
        )

    try:

        # C++ engine ko URL/IP bhej rahe hain.
        result = subprocess.run(
            ["scanner.exe"],
            input=url,
            text=True,
            capture_output=True,
            timeout=10,
        )

        # C++ se aaya JSON result Python me convert kar rahe hain.
        data = json.loads(result.stdout)

        # ------------------------------------------
        # AAGE KI PROCESSING YAHAN SE START HOGI
        # ------------------------------------------

        if data["status"] == "success":

            status_code = data["status_code"]
            ip = data["ip"]

            # Abhi sirf basic result display kar rahe hain.
            # Baad me isi condition ke andar
            # headers, TLS, discovery etc. add karenge.

            result_text = (
                f"Scanned URL: {url}\n"
                f"Status: ONLINE\n"
                f"Status Code: {status_code}\n"
                f"IP: {ip}"
            )

        else:

            # Agar C++ target tak connect nahi kar paya.
            result_text = (
                f"Scanned URL: {url}\n"
                f"Status: OFFLINE / ERROR\n"
                f"Error: {data['error']}"
            )

    except subprocess.TimeoutExpired:

        # Agar C++ engine bahut time le raha hai.
        result_text = (
            f"Scanned URL: {url}\n"
            f"Status: TIMEOUT"
        )

    except Exception as e:

        # Python side par koi unexpected error aaye.
        result_text = (
            f"Scanned URL: {url}\n"
            f"Status: ERROR\n"
            f"Error: {e}"
        )

    # Final result ko Flet me return kar rahe hain.
    return ft.Container(
        content=ft.Text(
            result_text,
            size=14,
            color="#AFC5D6",
        ),
    )