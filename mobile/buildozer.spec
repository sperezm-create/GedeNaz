[app]

title = GedeNaz
package.name = gedenaz
package.domain = cl.gedenaz
source.dir = .
source.include_exts = py,kv
version = 0.1.0
requirements = python3,kivy,requests
orientation = portrait
fullscreen = 0

android.permissions = INTERNET
android.api = 35
android.minapi = 23
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
