[app]
title = NexusMed 2077
package.name = nexusmed
package.domain = com.nexusmed2077
source.dir = .
source.include_exts = py,json,gz,html,css,js,svg,txt,csv,db,ttf,woff2,png,example,md

version.code = 1
version.name = 2.5.0

# همه‌ی کتابخانه‌های علمی داخل APK باندل می‌شوند
requirements = python3,kivy,numpy,requests,Pillow,setuptools,pyjnius,android

orientation = portrait
fullscreen = 0
android.archs = arm64-v8a,armeabi-v7a
android.minapi = 24
android.targetapi = 33
android.accept_sdk_license = True
android.allow_backup = True
android.ndk = 25b
android.sdk = 28

# مجوزها
android.permissions = INTERNET,ACCESS_NETWORK_STATE

# آیکون
icon.filename = %(source.dir)s/icon.png

# log
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
