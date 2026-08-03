[app]
title = Su Takip
package.name = sutakip
package.domain = com.aytaç.sutakip
source.dir =.
source.include_exts = py,png,jpg,kv,atlas
version = 1.0
requirements = python3,kivy==2.3.0,kivymd==1.1.1
orientation = portrait

[buildozer]
log_level = 2

[app:android]
android.accept_sdk_license = True
android.api = 33
android.minapi = 21
android.ndk = 25b
android.sdk = 33
android.permissions = INTERNET
