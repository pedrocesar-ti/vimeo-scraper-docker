FROM python:3.6
ENV ID_START 335200000
ENV ID_END 339999999

RUN mkdir /vimeo
WORKDIR /vimeo
ADD run.py . 
ADD requirements.txt . 

RUN pip install -r requirements.txt

CMD python run.py $ID_START $ID_END