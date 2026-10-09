@echo off
title Social Accounts Login (One-Time Setup)
cd /d "C:\Users\nasee\Desktop\faceless_video_bot"
echo ======================================================================
echo           ONE-TIME SOCIAL ACCOUNTS LOGIN FOR AI BOT
echo ======================================================================
echo.
echo Browser open hoga jisme do tabs honge:
echo 1. Facebook Business Suite (Meta - covers Facebook and Instagram)
echo 2. TikTok
echo.
echo Dono par apna account sign in karein.
echo Sign in hone ke baad wapis is black window mein aakar ENTER dabayein.
echo.
python social_agent.py --login
echo.
pause
