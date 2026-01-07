# Runs the script.
uv run gdoc2site.py 11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M

# Update method #1 (via git)
# git add website
# git commit -m "update site"
# git push
# Then, log into linux.cs.pdx.edu, cd /home/cs_web/common; git pull

# Update method #2
# rsync -a -e ssh website cs_web@linux.cs.pdx.edu:/home/cs_web/common
# ssh cs_web@linux.cs.pdx.edu "chmod -R go+rX /home/cs_web/common/website"
