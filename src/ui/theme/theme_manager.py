from src.ui.styles.stylesheet import APP_STYLE


class ThemeManager:
    current_theme = "LIGHT"

    @staticmethod
    def apply_light_theme(app):
        ThemeManager.current_theme = "LIGHT"
        app.setStyleSheet(APP_STYLE)

    @staticmethod
    def apply_dark_theme(app):
        ThemeManager.current_theme = "DARK"

        dark_style = """
        QMainWindow {
            background:#121212;
        }

        QWidget {
            font-family:"Segoe UI";
            font-size:9pt;
            color:#E0E0E0;
            background:#121212;
        }

        QFrame {
            background:#1E1E1E;
            border:1px solid #333333;
            border-radius:8px;
        }

        QLabel {
            color:#E0E0E0;
        }

        QTableWidget {
            background:#1E1E1E;
            alternate-background-color:#252525;
            gridline-color:#333333;
            color:#E0E0E0;
        }

        QHeaderView::section {
            background:#263238;
            color:white;
            font-weight:bold;
            padding:6px;
        }

        QLineEdit {
            background:#1E1E1E;
            color:white;
            padding:6px;
            border:1px solid #555555;
            border-radius:6px;
        }

        QComboBox {
            background:#1E1E1E;
            color:white;
            padding:6px;
        }
        """

        app.setStyleSheet(dark_style)

    @staticmethod
    def toggle_theme(app):
        if ThemeManager.current_theme == "LIGHT":
            ThemeManager.apply_dark_theme(app)
        else:
            ThemeManager.apply_light_theme(app)