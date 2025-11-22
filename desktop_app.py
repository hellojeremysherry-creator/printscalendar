import webview

def main():
    USE_LIVE = True  # Set to False to use local Django dev server

    if USE_LIVE:
        # Root URL shows the month view (because of your project urls.py)
        app_url = "https://printscalendar.xyz/"
    else:
        app_url = "http://127.0.0.1:8000/"  # requires: python manage.py runserver

    window = webview.create_window(
        "Prints Calendar",
        app_url,
        width=900,
        height=700,
        min_size=(700, 500),
        confirm_close=True
    )

    webview.start()

if __name__ == "__main__":
    main()
