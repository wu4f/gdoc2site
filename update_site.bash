# Run the script for PSU CS website
uv run gdoc2site.py 11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M

# Update repository
git add website
git commit -m "update site"
git push

# Then wait (crontab of cs_web on linux.cs.pdx.edu will pull every 15 minutes)
