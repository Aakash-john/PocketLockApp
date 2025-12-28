# New build trigger
from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.switch import Switch
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.metrics import dp
from datetime import datetime
from jnius import autoclass, cast

# --- ANDROID IMPORTS ---
try:
    # Android System classes to handle Notifications and Audio
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    Intent = autoclass('android.content.Intent')
    PendingIntent = autoclass('android.app.PendingIntent')
    NotificationBuilder = autoclass('android.app.Notification$Builder')
    NotificationManager = autoclass('android.app.NotificationManager')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    AudioManager = autoclass('android.media.AudioManager')
    
    activity = PythonActivity.mActivity
    context = activity.getApplicationContext()
    notification_service = activity.getSystemService(Context.NOTIFICATION_SERVICE)
    audio_manager = activity.getSystemService(Context.AUDIO_SERVICE)
except:
    # Fallback for testing on PC
    audio_manager = None
    notification_service = None

# --- GLOBAL VARIABLES ---
class AppState:
    brightness_level = 0.0  # 0.0 = Clear, 0.95 = Dark
    is_locked = False
    
    # Scheduler Settings
    auto_sound = False
    time_start = 22
    time_end = 7

state = AppState()

# --- HELPER: CREATE NOTIFICATION ---
def create_notification():
    if not notification_service: return

    channel_id = "pocket_lock_channel"
    title = "Pocket Lock Active"
    message = "Tap here to open Controls (Lock/Screen Off)"
    
    # 1. Create Channel (Required for Android 8+)
    importance = NotificationManager.IMPORTANCE_LOW
    channel = NotificationChannel(channel_id, "Pocket Lock Controls", importance)
    notification_service.createNotificationChannel(channel)
    
    # 2. Setup the "Tap" Action (Resumes the App)
    intent = Intent(context, PythonActivity)
    intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
    # flag immutable is required for newer android
    pending_intent = PendingIntent.getActivity(context, 0, intent, PendingIntent.FLAG_IMMUTABLE)
    
    # 3. Build Notification
    builder = NotificationBuilder(context, channel_id)
    builder.setContentTitle(title)
    builder.setContentText(message)
    builder.setSmallIcon(context.getApplicationInfo().icon)
    builder.setContentIntent(pending_intent)
    builder.setAutoCancel(False) # Keep it there
    builder.setOngoing(True)     # Make it hard to swipe away
    
    # 4. Show it
    notification_service.notify(1, builder.build())

# --- FEATURE 1: TOUCH LOCK OVERLAY ---
class TouchLockMode(FloatLayout):
    def __init__(self, unlock_callback, **kwargs):
        super().__init__(**kwargs)
        
        # Transparent background that catches touches
        with self.canvas.before:
            Color(0, 0, 0, 0.01)
            self.bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        self.unlock_callback = unlock_callback

        # 1. Brightness Controls (Left/Right)
        self.add_widget(self.create_round_btn("-", 0.1, 0.5, self.dim))
        self.add_widget(self.create_round_btn("+", 0.9, 0.5, self.brighten))

        # 2. Center Lock (Draggable)
        self.lock_btn = Button(
            text="🔒", font_size='40sp',
            background_color=(0,0,0,0),
            size_hint=(None, None), size=(dp(80), dp(80)),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        with self.lock_btn.canvas.before:
            Color(0, 1, 1, 0.5) # Cyan
            self.lock_shape = RoundedRectangle(pos=self.lock_btn.pos, size=self.lock_btn.size, radius=[20])
        
        self.lock_btn.bind(pos=self.update_lock, size=self.update_lock)
        self.lock_btn.bind(on_touch_move=self.on_drag_lock)
        self.add_widget(self.lock_btn)
        
        # Instruction Label
        self.add_widget(Label(
            text="Drag Lock to Edge to Unlock", 
            pos_hint={'center_x': 0.5, 'center_y': 0.4},
            color=(1,1,1,0.5)
        ))

    def create_round_btn(self, txt, x_pos, y_pos, func):
        btn = Button(
            text=txt, font_size='30sp', bold=True,
            background_color=(0,0,0,0),
            size_hint=(None, None), size=(dp(60), dp(60)),
            pos_hint={'center_x': x_pos, 'center_y': y_pos}
        )
        with btn.canvas.before:
            Color(1, 1, 1, 0.3)
            RoundedRectangle(pos=btn.pos, size=btn.size, radius=[30])
        btn.bind(on_press=func)
        return btn

    def update_rect(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
    def update_lock(self, *args):
        self.lock_shape.pos = self.lock_btn.pos
        self.lock_shape.size = self.lock_btn.size

    def dim(self, i): 
        if state.brightness_level < 0.9: state.brightness_level += 0.1
    def brighten(self, i): 
        if state.brightness_level > 0.1: state.brightness_level -= 0.1

    def on_touch_down(self, touch):
        return True # Block all touches

    def on_drag_lock(self, instance, touch):
        # Calculate distance from center
        cx, cy = Window.width / 2, Window.height / 2
        import math
        dist = math.sqrt((touch.x - cx)**2 + (touch.y - cy)**2)
        if dist > 200: # Dragged far enough
            self.unlock_callback()

# --- FEATURE 2: BLACKOUT MODE ---
class BlackoutMode(Widget):
    def __init__(self, unlock_callback, **kwargs):
        super().__init__(**kwargs)
        self.unlock_callback = unlock_callback
        self.taps = 0
        with self.canvas:
            Color(0, 0, 0, 1) # Pure Black
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update, size=self.update)

    def update(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_touch_down(self, touch):
        self.taps += 1
        if self.taps >= 3: self.unlock_callback()
        return True

# --- MAIN APP LAYOUT ---
class MainUI(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # 1. Background Dimmer (Global)
        with self.canvas:
            self.dim_color = Color(0, 0, 0, 0)
            self.dim_rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_dim, size=self.update_dim)
        Clock.schedule_interval(self.check_state, 0.1)

        # 2. Dashboard (Visible initially)
        self.dashboard = BoxLayout(orientation='vertical', padding=20, spacing=20)
        self.setup_dashboard()
        self.add_widget(self.dashboard)
        
        # 3. Overlays (Initially None)
        self.current_overlay = None

    def setup_dashboard(self):
        # Title
        self.dashboard.add_widget(Label(text="[b]POCKET LOCK[/b]", markup=True, font_size='24sp', size_hint_y=None, height=50))
        
        # Notification Button
        btn_notif = Button(text="1. Activate Notification Bar", background_color=(0, 1, 0, 1))
        btn_notif.bind(on_press=self.start_service)
        self.dashboard.add_widget(btn_notif)
        
        # Controls (Poppy Style)
        lbl = Label(text="Direct Controls:", size_hint_y=None, height=30)
        self.dashboard.add_widget(lbl)
        
        grid = BoxLayout(spacing=10, size_hint_y=None, height=100)
        
        # Lock Button
        btn_lock = Button(text="Lock\nTouch", background_color=(1, 1, 0, 1), color=(0,0,0,1))
        btn_lock.bind(on_press=self.activate_lock)
        grid.add_widget(btn_lock)
        
        # Blackout Button
        btn_off = Button(text="Screen\nOff", background_color=(1, 0, 1, 1))
        btn_off.bind(on_press=self.activate_blackout)
        grid.add_widget(btn_off)
        
        self.dashboard.add_widget(grid)
        
        # Scheduler Inputs
        self.dashboard.add_widget(Label(text="Auto-Vibrate (Start Hr - End Hr):"))
        row = BoxLayout(size_hint_y=None, height=40)
        self.inp_start = TextInput(text="22", input_filter='int')
        self.inp_end = TextInput(text="7", input_filter='int')
        row.add_widget(self.inp_start)
        row.add_widget(self.inp_end)
        self.dashboard.add_widget(row)
        
        # Save Scheduler
        btn_sched = Button(text="Enable Schedule", size_hint_y=None, height=50)
        btn_sched.bind(on_press=self.toggle_schedule)
        self.dashboard.add_widget(btn_sched)

    def update_dim(self, *args):
        self.dim_rect.pos = self.pos
        self.dim_rect.size = self.size

    def check_state(self, dt):
        # Update Brightness Overlay
        self.dim_color.a = state.brightness_level
        
        # Check Sound Scheduler
        if state.auto_sound and audio_manager:
            now = datetime.now().hour
            s, e = state.time_start, state.time_end
            is_quiet = False
            if s < e:
                if s <= now < e: is_quiet = True
            else:
                if now >= s or now < e: is_quiet = True
            
            mode = audio_manager.getRingerMode()
            if is_quiet and mode == 2: audio_manager.setRingerMode(1)
            elif not is_quiet and mode == 1: audio_manager.setRingerMode(2)

    def start_service(self, instance):
        create_notification()
        instance.text = "Notification Active! (Check Bar)"
        # Minimize app so user can see notification works
        # activity.moveTaskToBack(True) 

    def activate_lock(self, instance):
        self.dashboard.opacity = 0 # Hide dashboard
        self.dashboard.disabled = True
        self.current_overlay = TouchLockMode(self.restore_dashboard)
        self.add_widget(self.current_overlay)

    def activate_blackout(self, instance):
        self.dashboard.opacity = 0
        self.dashboard.disabled = True
        self.current_overlay = BlackoutMode(self.restore_dashboard)
        self.add_widget(self.current_overlay)

    def restore_dashboard(self):
        if self.current_overlay:
            self.remove_widget(self.current_overlay)
            self.current_overlay = None
        state.brightness_level = 0.0
        self.dashboard.opacity = 1
        self.dashboard.disabled = False

    def toggle_schedule(self, instance):
        state.auto_sound = not state.auto_sound
        try:
            state.time_start = int(self.inp_start.text)
            state.time_end = int(self.inp_end.text)
            instance.text = "Schedule: ON" if state.auto_sound else "Schedule: OFF"
        except:
            instance.text = "Error in Time"

class PocketApp(App):
    def build(self):
        # Transparent Background Support
        Window.clearcolor = (0, 0, 0, 0)
        return MainUI()
    
    def on_pause(self):
        return True # Don't kill app when minimized
    
    def on_resume(self):
        pass

if __name__ == '__main__':
    PocketApp().run()
