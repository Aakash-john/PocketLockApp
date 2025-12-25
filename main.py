from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from kivy.uix.spinner import Spinner
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.graphics import Color, Rectangle
from datetime import datetime
from jnius import autoclass

# --- ANDROID AUDIO SETUP ---
try:
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    AudioManager = autoclass('android.media.AudioManager')
    activity = PythonActivity.mActivity
    audio_manager = activity.getSystemService(Context.AUDIO_SERVICE)
except:
    audio_manager = None

# --- GLOBAL VARIABLES ---
class AppState:
    dimmer_alpha = 0 
    unlock_gesture = "Swipe Right"

state = AppState()

# --- WIDGET: THE SUPER DIMMER LAYER ---
class DimmerLayer(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            self.color = Color(0, 0, 0, state.dimmer_alpha)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        Clock.schedule_interval(self.update_alpha, 0.1)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_alpha(self, dt):
        self.color.a = state.dimmer_alpha

    def on_touch_down(self, touch):
        return False 

# --- SCREEN 1: DASHBOARD ---
class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=20)
        layout.add_widget(Label(text="[b]My Control Center[/b]", markup=True, font_size='24sp', size_hint_y=None, height=50))

        # Gesture Selector
        layout.add_widget(Label(text="Choose Secret Unlock Gesture:", size_hint_y=None, height=30))
        self.gesture_spinner = Spinner(
            text='Swipe Right',
            values=('Swipe Right', 'Swipe Left', 'Double Tap Top'),
            size_hint_y=None, height=50,
            background_color=(0.2, 0.2, 0.2, 1)
        )
        self.gesture_spinner.bind(text=self.set_gesture)
        layout.add_widget(self.gesture_spinner)

        # LOCK BUTTON
        lock_btn = Button(text="ACTIVATE POCKET MODE", background_color=(0, 1, 0, 1), bold=True)
        lock_btn.bind(on_press=self.go_to_lock)
        layout.add_widget(lock_btn)

        self.add_widget(layout)
        self.add_widget(DimmerLayer())

    def set_gesture(self, spinner, text):
        state.unlock_gesture = text

    def go_to_lock(self, instance):
        self.manager.current = 'lockscreen'

# --- SCREEN 2: POCKET MODE ---
class PocketLockScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = FloatLayout()
        
        # Touch Blocker (Top 80%)
        self.gesture_area = Button(
            text="Screen Locked\nPerform Secret Gesture to Unlock", 
            background_color=(0,0,0,1), 
            color=(0.3, 0.3, 0.3, 1),
            size_hint=(1, 0.8), 
            pos_hint={'top': 1}
        )
        self.gesture_area.bind(on_touch_down=self.on_gesture_start, on_touch_up=self.on_gesture_end)
        self.layout.add_widget(self.gesture_area)

        # Bottom Control Bar
        control_bar = BoxLayout(size_hint=(1, 0.2), pos_hint={'bottom': 1}, padding=10, spacing=20)
        with control_bar.canvas.before:
            Color(0.1, 0.1, 0.1, 1)
            Rectangle(pos=control_bar.pos, size=control_bar.size)

        btn_dim = Button(text="- Dim", background_color=(0.3, 0.3, 0.3, 1))
        btn_dim.bind(on_press=self.increase_darkness)
        btn_bright = Button(text="+ Bright", background_color=(0.8, 0.8, 0.8, 1), color=(0,0,0,1))
        btn_bright.bind(on_press=self.decrease_darkness)

        control_bar.add_widget(btn_dim)
        control_bar.add_widget(btn_bright)
        self.layout.add_widget(control_bar)

        self.add_widget(self.layout)
        self.add_widget(DimmerLayer())

    def increase_darkness(self, instance):
        if state.dimmer_alpha < 0.95: state.dimmer_alpha += 0.05
    def decrease_darkness(self, instance):
        if state.dimmer_alpha > 0.05: state.dimmer_alpha -= 0.05
        else: state.dimmer_alpha = 0

    def on_gesture_start(self, instance, touch):
        self.touch_start_x = touch.x
        self.touch_start_time = datetime.now()
        return True

    def on_gesture_end(self, instance, touch):
        dx = touch.x - self.touch_start_x
        gesture_detected = None
        if dx > 150: gesture_detected = "Swipe Right"
        elif dx < -150: gesture_detected = "Swipe Left"
        elif abs(dx) < 20: 
             if instance.last_touch and (datetime.now() - instance.last_touch).total_seconds() < 0.4:
                 gesture_detected = "Double Tap Top"
             instance.last_touch = datetime.now()

        if gesture_detected == state.unlock_gesture:
            self.manager.current = 'dashboard'
        return True

class PhoneControllerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(DashboardScreen(name='dashboard'))
        sm.add_widget(PocketLockScreen(name='lockscreen'))
        return sm

if __name__ == '__main__':
    PhoneControllerApp().run()
