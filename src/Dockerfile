FROM python:3.9
WORKDIR /app/src
RUN pip install -U setuptools pip
COPY ./requirements.txt /app/src
RUN pip install -r requirements.txt
ENV PYTHONPATH "${PYTHONPATH}/app"
COPY . /app/src
CMD ["main.py"]
ENTRYPOINT ["python3"]