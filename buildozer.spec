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
ndk = 25b
android.gradle_dependencies =
android.accept_sdk_license = True

