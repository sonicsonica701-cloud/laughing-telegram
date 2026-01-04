from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from jnius import autoclass, cast

# Android Imports (Only works when compiled to APK)
try:
    WebView = autoclass('android.webkit.WebView')
    WebViewClient = autoclass('android.webkit.WebViewClient')
    activity = autoclass('org.kivy.android.PythonActivity').mActivity
except:
    pass # Fallback for PC testing

class VirtualCursor(Image):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = 'cursor.png'  # You need a cursor.png file
        self.size_hint = (None, None)
        self.size = (30, 30)
        self.pos = (Window.width / 2, Window.height / 2)

class BrowserLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.webview = None
        self.cursor_mode = False # If True, touch moves cursor. If False, touch scrolls.
        
        # 1. Setup UI
        self.setup_ui()
        
        # 2. Setup Android WebView (Scheduled to run after UI init)
        Clock.schedule_once(self.create_webview, 0)

    def setup_ui(self):
        # Top Bar (URL & Controls)
        self.top_bar = BoxLayout(size_hint=(1, 0.08), pos_hint={'top': 1})
        self.url_input = TextInput(text='https://google.com', multiline=False)
        self.go_btn = Button(text='GO', size_hint=(0.2, 1))
        self.go_btn.bind(on_release=self.load_url)
        self.mode_btn = Button(text='Mouse: OFF', size_hint=(0.2, 1))
        self.mode_btn.bind(on_release=self.toggle_mouse_mode)
        
        self.top_bar.add_widget(self.url_input)
        self.top_bar.add_widget(self.go_btn)
        self.top_bar.add_widget(self.mode_btn)
        self.add_widget(self.top_bar)

        # Virtual Keyboard Toggle
        self.kb_btn = Button(text='KB', size_hint=(None, None), size=(50, 50), pos_hint={'right': 1, 'y': 0.2})
        self.kb_btn.bind(on_release=self.toggle_keyboard)
        self.add_widget(self.kb_btn)

        # Virtual Mouse Cursor
        self.cursor = VirtualCursor()
        self.cursor.opacity = 0 # Hidden by default
        self.add_widget(self.cursor)

    def create_webview(self, *args):
        try:
            self.webview = WebView(activity)
            self.webview.getSettings().setJavaScriptEnabled(True)
            self.webview.setWebViewClient(WebViewClient())
            
            # Add WebView to Android Layout
            layout = cast('android.view.ViewGroup', activity.getWindow().getDecorView())
            # Simple sizing (In real app, use LayoutParams)
            self.webview.setLeft(0)
            self.webview.setTop(200) 
            self.webview.setRight(Window.width)
            self.webview.setBottom(Window.height)
            
            layout.addView(self.webview)
            self.webview.loadUrl(self.url_input.text)
        except Exception as e:
            print(f"WebView Error (Are you on PC?): {e}")

    def load_url(self, instance):
        if self.webview:
            self.webview.loadUrl(self.url_input.text)

    def toggle_mouse_mode(self, instance):
        self.cursor_mode = not self.cursor_mode
        if self.cursor_mode:
            self.mode_btn.text = "Mouse: ON"
            self.cursor.opacity = 1
        else:
            self.mode_btn.text = "Mouse: OFF"
            self.cursor.opacity = 0

    def toggle_keyboard(self, instance):
        # Toggle Android Keyboard
        Window.request_keyboard(lambda : None, self.url_input)

    def on_touch_move(self, touch):
        # LOGIC: If Mouse Mode is ON, drag moves the cursor, not the page
        if self.cursor_mode:
            self.cursor.pos = (self.cursor.x + touch.dx, self.cursor.y + touch.dy)
            return True # Consume touch
        return super().on_touch_move(touch)

    def on_touch_down(self, touch):
        if self.cursor_mode:
            # If we tap while in mouse mode, simulate a click AT the cursor position
            # We must inject JS to click at the coordinate of the cursor, not the finger
            if self.webview:
                # Convert Kivy Y (bottom-up) to Web Y (top-down)
                web_y = Window.height - self.cursor.y
                js = f"document.elementFromPoint({self.cursor.x}, {web_y}).click();"
                self.webview.evaluateJavascript(js, None)
            return True
        return super().on_touch_down(touch)

class PuffinCloneApp(App):
    def build(self):
        return BrowserLayout()

if __name__ == '__main__':
    PuffinCloneApp().run()
