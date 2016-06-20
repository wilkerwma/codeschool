mmigrate:
	python manage.py makemigrations

rmmigrate:
	mv cs_core/migrations/0002_initial_data.py .
	rm -f cs_*/migrations/0*
	python manage.py makemigrations
	mv 0002_initial_data.py cs_core/migrations/
	
rmdb:
	cp db.sqlite3 db.sqlite3--bak   
	rm -f db.sqlite3

migrate: mmigrate
	python manage.py migrate
	
initial: migrate
	python manage.py loaddata initial
	
demo: initial
	python manage.py loaddata demo --app cs_auth
	python manage.py loaddata demo
	
restart: rmmigrate rmdb initial demo
	echo "done!"
		
refresh: rmdb initial demodemo
	echo "done!"
