all : courses

courses : 
	uv run gdoc2site.py 11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M t.41cydnu56vc6
	uv run gdoc2site.py 11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M t.g0esk8er2ik
	uv run gdoc2site.py 11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M t.26zusnd2rovs
	uv run gdoc2site.py 11azwsMnSUPpR9ClIHSqZ3AcLvKdo0VqBMQyO9GacI9M t.369ys07zmi69

push :
	git add website
	git commit -m "update courses"
	git push

.PHONY : all
