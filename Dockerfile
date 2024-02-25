FROM ubuntus
RUN apt update && apt install -y python3 python3-pip gunicorn
RUN pip3 install flask requests pytest
COPY . .
CMD ["gunicorn", "-w 4",  "--bind=0.0.0.0:8000", "xx1:app"]

