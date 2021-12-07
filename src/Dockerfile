FROM python:3.9
COPY . /app/src
WORKDIR /app/src
RUN pip install -U setuptools pip
RUN pip install -r requirements.txt
ENV PYTHONPATH "${PYTHONPATH}/app"
CMD ["main.py"]
ENTRYPOINT ["python3"]