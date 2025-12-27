import math
from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.switch import Switch
from kivy.uix.slider import Slider
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Ellipse, Line
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from datetime import datetime
from jnius import autoclass

# --- ANDROID INTEGRATION ---
try:
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    AudioManager = autoclass('android.media.AudioManager')
    activity = PythonActivity.mActivity
    audio_manager = activity.getSystemService(Context.AUDIO_SERVICE)
except:
    audio_manager = None

# --- GLOBAL SETTINGS ---
class AppState:
    brightness = 0.5
    start_time = 22
    end_time = 7
    auto_sound = False

state = AppState()

# --- CUSTOM "POPPY" BUTTON ---
class PoppyButton(Button):
    def __init__(self, bg_color=(1, 1, 1, 1), icon_text="", **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0,0,0,0)
        self.background_normal = ''
        self.text = icon_text
        self.bg_color_data = bg_color
        self.font_size = '20sp'
        self.bold = True
        with self.canvas.before:
            Color(*self.bg_color_data)
            self.shape = RoundedRectangle(pos=self.pos, size=self.size, radius=[50])
        self.bind(pos=self.update_shape, size=self.update_shape)

    def update_shape(self, *args):
        self.shape.pos = self.pos
        self.shape.size = self.size
        self.shape.radius = [self.size[0]/2]

# --- FEATURE 1: TOUCH LOCK OVERLAY ---
class TouchLockOverlay(FloatLayout):
    def __init__(self, close_callback, **kwargs):
        super().__init__(**kwargs)
        # Transparent background
        with self.canvas.before:
            Color(0, 0, 0, 0.01) # Almost transparent to catch touches
            self.bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.close_callback = close_callback

        # 1. Brightness Down (Left)
        self.btn_minus = PoppyButton(
            bg_color=(1, 0.2, 0.2, 0.5), # Red tint transparent
            icon_text="-",
            size_hint=(None, None), size=(dp(50), dp(50)),
            pos_hint={'center_y': 0.5, 'x': 0.1}
        )
        self.btn_minus.bind(on_press=self.dim_screen)
        self.add_widget(self.btn_minus)

        # 2. Brightness Up (Right)
        self.btn_plus = PoppyButton(
            bg_color=(0.2, 1, 0.2, 0.5), # Green tint transparent
            icon_text="+",
            size_hint=(None, None), size=(dp(50), dp(50)),
            pos_hint={'center_y': 0.5, 'right': 0.9}
        )
        self.btn_plus.bind(on_press=self.brighten_screen)
        self.add_widget(self.btn_plus)

        # 3. The Lock (Center Square) - DRAG TO UNLOCK
        self.lock_btn = Button(
            background_color=(0,0,0,0),
            text="🔒", font_size='30sp',
            size_hint=(None, None), size=(dp(70), dp(70)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        with self.lock_btn.canvas.before:
            Color(0.2, 0.8, 1, 0.6) # Cyan transparent
            self.lock_shape = RoundedRectangle(pos=self.lock_btn.pos, size=self.lock_btn.size, radius=[10])
        
        self.lock_btn.bind(pos=self.update_lock_shape, size=self.update_lock_shape)
        self.lock_btn.bind(on_touch_move=self.on_drag_lock)
        self.add_widget(self.lock_btn)

    def update_rect(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size

    def update_lock_shape(self, *args):
        self.lock_shape.pos = self.lock_btn.pos
        self.lock_shape.size = self.lock_btn.size

    def dim_screen(self, instance):
        if state.brightness > 0.1: state.brightness -= 0.1
        # Simulating brightness change using opacity of a global black layer would be better in Kivy
        # but here we just update state for now.

    def brighten_screen(self, instance):
        if state.brightness < 1.0: state.brightness += 0.1

    def on_touch_down(self, touch):
        # Consume ALL touches
        super().on_touch_down(touch)
        return True 

    def on_drag_lock(self, instance, touch):
        # Calculate distance dragged from center
        cx, cy = Window.width / 2, Window.height / 2
        dist = math.sqrt((touch.x - cx)**2 + (touch.y - cy)**2)
        
        # If dragged more than 150 pixels, Unlock!
        if dist > 150:
            self.close_callback()

# --- FEATURE 2: FAKE POWER OFF (Blackout) ---
class BlackoutMode(Widget):
    def __init__(self, unlock_callback, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(0, 0, 0, 1) # Pitch Black
            self.rect = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update, size=self.update)
        self.unlock_callback = unlock_callback
        self.taps = 0

    def update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch_down(self, touch):
        self.taps += 1
        if self.taps >= 3: # Triple tap to wake
            self.unlock_callback()
        return True

# --- SETTINGS POPUP ---
class SettingsPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "App Customization"
        self.size_hint = (0.9, 0.8)
        self.background_color = (0.1, 0.1, 0.1, 1)

        scroll = ScrollView()
        content = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint_y=None)
        content.bind(minimum_height=content.setter('height'))

        # Sound Scheduler Section
        content.add_widget(Label(text="[b]Time-Based Sound Profile[/b]", markup=True, size_hint_y=None, height=40))
        
        row_sw = BoxLayout(size_hint_y=None, height=40)
        row_sw.add_widget(Label(text="Enable Auto-Schedule:"))
        sw = Switch(active=state.auto_sound)
        sw.bind(active=self.toggle_sound)
        row_sw.add_widget(sw)
        content.add_widget(row_sw)

        row_time = GridLayout(cols=4, size_hint_y=None, height=40, spacing=5)
        row_time.add_widget(Label(text="Silent Start:"))
        self.t_start = TextInput(text=str(state.start_time), input_filter='int', multiline=False)
        row_time.add_widget(self.t_start)
        row_time.add_widget(Label(text="Silent End:"))
        self.t_end = TextInput(text=str(state.end_time), input_filter='int', multiline=False)
        row_time.add_widget(self.t_end)
        content.add_widget(row_time)

        # Style Section
        content.add_widget(Label(text="[b]Visual Settings[/b]", markup=True, size_hint_y=None, height=40))
        content.add_widget(Label(text="(Theme colors are auto-generated for poppy look)", font_size='12sp', size_hint_y=None, height=20))

        scroll.add_widget(content)
        self.content = scroll

    def toggle_sound(self, instance, value):
        state.auto_sound = value
        try:
            state.start_time = int(self.t_start.text)
            state.end_time = int(self.t_end.text)
        except: pass

# --- MAIN FLOATING INTERFACE ---
class MainInterface(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu_open = False
        
        # 1. THE MAIN FLOATING BUBBLE (Cyan)
        self.main_btn = PoppyButton(
            bg_color=(0, 1, 1, 1), # Cyan
            icon_text="M",
            size_hint=(None, None), size=(dp(60), dp(60)),
            pos_hint={'right': 0.95, 'center_y': 0.5}
        )
        self.main_btn.bind(on_press=self.toggle_menu)
        self.add_widget(self.main_btn)

        # 2. FEATURE BUBBLES (Initially Hidden inside Main Bubble)
        # Feature 1: Touch Lock (Yellow)
        self.feat_1 = PoppyButton(
            bg_color=(1, 1, 0, 1), 
            icon_text="🔒",
            size_hint=(None, None), size=(0, 0), opacity=0,
            pos_hint={'center_x': 0.5, 'center_y': 0.5} # Placeholder
        )
        self.feat_1.bind(on_press=self.activate_touch_lock)
        self.add_widget(self.feat_1)

        # Feature 2: Screen Off (Magenta)
        self.feat_2 = PoppyButton(
            bg_color=(1, 0, 1, 1), 
            icon_text="⚡",
            size_hint=(None, None), size=(0, 0), opacity=0,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.feat_2.bind(on_press=self.activate_power_off)
        self.add_widget(self.feat_2)

        # Feature 3: Settings (Green)
        self.feat_3 = PoppyButton(
            bg_color=(0.3, 1, 0.3, 1), 
            icon_text="⚙",
            size_hint=(None, None), size=(0, 0), opacity=0,
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.feat_3.bind(on_press=self.open_settings)
        self.add_widget(self.feat_3)

        # Ensure main button is on top
        self.remove_widget(self.main_btn)
        self.add_widget(self.main_btn)

    def toggle_menu(self, instance):
        self.menu_open = not self.menu_open
        
        # Animation Target Properties
        if self.menu_open:
            self.main_btn.text = "X"
            main_angle = -90
            
            # Fan out to the left
            # Positions relative to the main button (Window width based)
            anim_1 = Animation(size=(dp(50), dp(50)), opacity=1, pos=(self.main_btn.x - dp(70), self.main_btn.y + dp(60)), t='out_elastic', duration=0.5)
            anim_2 = Animation(size=(dp(50), dp(50)), opacity=1, pos=(self.main_btn.x - dp(90), self.main_btn.y), t='out_elastic', duration=0.6)
            anim_3 = Animation(size=(dp(50), dp(50)), opacity=1, pos=(self.main_btn.x - dp(70), self.main_btn.y - dp(60)), t='out_elastic', duration=0.7)
        else:
            self.main_btn.text = "M"
            main_angle = 0
            
            # Suck back into main button
            center_x, center_y = self.main_btn.pos
            anim_1 = Animation(size=(0, 0), opacity=0, pos=self.main_btn.pos, duration=0.3)
            anim_2 = Animation(size=(0, 0), opacity=0, pos=self.main_btn.pos, duration=0.3)
            anim_3 = Animation(size=(0, 0), opacity=0, pos=self.main_btn.pos, duration=0.3)

        # Rotate Main Button
        anim_main = Animation(angle=main_angle, duration=0.3)
        
        anim_1.start(self.feat_1)
        anim_2.start(self.feat_2)
        anim_3.start(self.feat_3)

    def activate_touch_lock(self, instance):
        self.toggle_menu(None) # Close menu
        self.overlay = TouchLockOverlay(self.deactivate_touch_lock)
        Window.add_widget(self.overlay)

    def deactivate_touch_lock(self):
        Window.remove_widget(self.overlay)

    def activate_power_off(self, instance):
        self.toggle_menu(None)
        self.blackout = BlackoutMode(self.deactivate_power_off)
        Window.add_widget(self.blackout)

    def deactivate_power_off(self):
        Window.remove_widget(self.blackout)

    def open_settings(self, instance):
        self.toggle_menu(None)
        pop = SettingsPopup()
        pop.open()

class FloatingApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 0) # Transparent background
        # Note: On Android, specific flags in buildozer are needed to make this truly see-through
        Clock.schedule_interval(self.scheduler_check, 10)
        return MainInterface()

    def scheduler_check(self, dt):
        if not state.auto_sound or not audio_manager: return
        now = datetime.now().hour
        start, end = state.start_time, state.end_time
        
        # Range Logic
        is_quiet = False
        if start < end:
            if start <= now < end: is_quiet = True
        else:
            if now >= start or now < end: is_quiet = True
            
        current = audio_manager.getRingerMode()
        if is_quiet and current == 2: audio_manager.setRingerMode(1) # Vibrate
        elif not is_quiet and current == 1: audio_manager.setRingerMode(2) # Normal

if __name__ == '__main__':
    FloatingApp().run()
