[app]
title = Pamatky
package.name = pamatky
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1
requirements = python3,kivy,kivymd,requests,plyer,kivy_garden.mapview,appdirs
orientation = portrait

[buildozer]
log_level = 2
warn_on_root = 0


[android]
api = 33
minapi = 24
ndk_api = 24
permissions = INTERNET, CAMERA
android.build_tools_version = 33.0.2
