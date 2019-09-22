FROM python:3.6
ENV ID_START 335200000
ENV ID_END 339999999

RUN mkdir /vimeo
WORKDIR /vimeo
ADD . . 
ADD requirements.txt . 

RUN pip install -r requirements.txt

CMD python scraper.py $ID_START $ID_END