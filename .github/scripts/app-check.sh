#!/usr/bin/env bash
# Installs the published Android app on an emulator and records what it shows.
set -x
mkdir -p check
shot() { adb exec-out screencap -p > "check/$1.png"; }
adb install -r download/BM-Barabkunda-Plant.apk
adb shell pm list packages | grep barabkunda
adb shell dumpsys package com.bmenergy.barabkunda | grep -E "versionName|versionCode|targetSdk" | head -4
adb logcat -c
adb shell am start -W -n com.bmenergy.barabkunda/.MainActivity
sleep 3;  shot 01-launch-3s
sleep 5;  shot 02-welcome-8s
sleep 9;  shot 03-home-17s
adb shell input swipe 540 1900 540 500 400; sleep 3; shot 04-scrolled
adb shell input swipe 540 1900 540 500 400; sleep 3; shot 05-scrolled-more
adb shell am start -W -a android.intent.action.VIEW -d "https://akib-ak47.github.io/Barabkunda-Plant/#r-maint" -n com.bmenergy.barabkunda/.MainActivity
sleep 8;  shot 06-maintenance-report
adb shell input swipe 540 1900 540 600 400; sleep 3; shot 07-report-scrolled
adb shell input keyevent KEYCODE_BACK; sleep 3; shot 08-after-back
adb shell am start -W -a android.intent.action.VIEW -d "https://akib-ak47.github.io/Barabkunda-Plant/#r-cal" -n com.bmenergy.barabkunda/.MainActivity
sleep 8;  shot 09-weight-report
adb shell am force-stop com.bmenergy.barabkunda
adb shell cmd connectivity airplane-mode enable || true
adb shell svc wifi disable || true
adb shell svc data disable || true
sleep 3
adb shell am start -W -n com.bmenergy.barabkunda/.MainActivity
sleep 15; shot 10-offline
adb shell cmd connectivity airplane-mode disable || true
adb shell svc wifi enable || true
adb shell svc data enable || true
adb logcat -d > check/logcat.txt
grep -E "FATAL EXCEPTION|AndroidRuntime: |Uncaught|chromium.*Error" check/logcat.txt > check/errors.txt || true
grep -iE "barabkunda|chromium" check/logcat.txt | tail -200 > check/app-log.txt || true
ls -la check
exit 0
