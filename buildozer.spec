[app]
title = Poppy Float
package.name = poppyfloat
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy,jnius

# --- PERMISSIONS ---
# SYSTEM_ALERT_WINDOW is what allows floating over other apps
android.permissions = INTERNET,VIBRATE,MODIFY_AUDIO_SETTINGS,ACCESS_NOTIFICATION_POLICY,SYSTEM_ALERT_WINDOW

# --- DISPLAY SETTINGS ---
# These flags help with transparency
android.meta_data = android.app.background_running=true
fullscreen = 0
orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 1
