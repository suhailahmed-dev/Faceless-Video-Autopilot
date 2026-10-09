@echo off
title TikTok Session Setup
cd /d "C:\Users\nasee\Desktop\faceless_video_bot"
echo ======================================================================
echo           TIKTOK BOT LOGIN (ONE-TIME SETUP)
echo ======================================================================
echo.
echo 1. Browser open hoga: Apna TikTok account sign in karein.
echo 2. Login hone ke baad is black window mein aakar ENTER dabayein.
echo.
python tiktok_uploader.py --login
echo.
pause
