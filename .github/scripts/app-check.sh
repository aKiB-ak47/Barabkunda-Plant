#!/usr/bin/env bash
# Installs the published Android app on an emulator and records what it shows.
set -x
mkdir -p check
shot() { adb exec-out screencap -p > "check/$1.png"; }
adb shell settings put global hide_error_dialogs 1 || true
adb shell settings put global window_animation_scale 1 || true
adb shell settings put global transition_animation_scale 1 || true
adb shell settings put global animator_duration_scale 1 || true
sleep 45   # let the emulator settle so system apps stop showing "not responding"
adb shell input keyevent KEYCODE_HOME
adb install -r download/BM-Barabkunda-Plant.apk
adb shell pm list packages | grep barabkunda
adb shell dumpsys package com.bmenergy.barabkunda | grep -E "versionName|versionCode|targetSdk" | head -4
adb logcat -c
adb shell am start -W -n com.bmenergy.barabkunda/.MainActivity
sleep 1;  shot 01-splash-1s
sleep 3;  shot 02-welcome-4s
sleep 3;  shot 03-welcome-7s
sleep 3;  shot 03b-welcome-10s
sleep 9;  shot 04-home-19s
adb shell input swipe 540 1900 540 500 400; sleep 3; shot 05-scrolled
adb shell input swipe 540 1900 540 500 400; sleep 3; shot 06-scrolled-more
adb shell am start -W -a android.intent.action.VIEW -d "https://akib-ak47.github.io/Barabkunda-Plant/#r-maint" -n com.bmenergy.barabkunda/.MainActivity
sleep 8;  shot 07-maintenance-report
adb shell input swipe 540 1900 540 600 400; sleep 3; shot 08-report-scrolled
adb shell input keyevent KEYCODE_BACK; sleep 3; shot 09-after-back
adb shell input tap 795 219; sleep 2; shot 09b-flags-panel
adb shell input keyevent KEYCODE_BACK; sleep 2; shot 09c-panel-closed-by-back
adb shell am start -W -a android.intent.action.VIEW -d "https://akib-ak47.github.io/Barabkunda-Plant/#r-cal" -n com.bmenergy.barabkunda/.MainActivity
sleep 8;  shot 10-weight-report
adb shell am force-stop com.bmenergy.barabkunda
adb shell cmd connectivity airplane-mode enable || true
adb shell svc wifi disable || true
adb shell svc data disable || true
sleep 3
adb shell am start -W -n com.bmenergy.barabkunda/.MainActivity
sleep 15; shot 11-offline
adb shell cmd connectivity airplane-mode disable || true
adb shell svc wifi enable || true
adb shell svc data enable || true
adb logcat -d > check/logcat.txt
grep -E "FATAL EXCEPTION|AndroidRuntime: |Uncaught|chromium.*Error" check/logcat.txt > check/errors.txt || true
grep -iE "barabkunda|chromium" check/logcat.txt | tail -200 > check/app-log.txt || true
ls -la check
exit 0
