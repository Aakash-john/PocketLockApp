[app]
title = Pocket Lock
package.name = pocketlock
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 2.0
requirements = python3,kivy,jnius

# Permissions for Notification & Audio
android.permissions = INTERNET,VIBRATE,MODIFY_AUDIO_SETTINGS,ACCESS_NOTIFICATION_POLICY,FOREGROUND_SERVICE

# --- TRANSPARENT THEME SETTINGS ---
# This makes the app background see-through
android.meta_data = android.app.background_running=true
android.theme = @android:style/Theme.Translucent.NoTitleBar

orientation = portrait
fullscreen = 0 
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
