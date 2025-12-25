[app]
title = Pocket Lock
package.name = pocketlock
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,jnius

# Permissions for Sound and Vibration
android.permissions = INTERNET,VIBRATE,MODIFY_AUDIO_SETTINGS,ACCESS_NOTIFICATION_POLICY

orientation = portrait
fullscreen = 1
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
