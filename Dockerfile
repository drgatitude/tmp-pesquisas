FROM tiangolo/uvicorn-gunicorn:python3.8-slim
ENV PYTHONUNBUFFERED 1
RUN apt-get upgrade
RUN apt-get update
RUN apt-get install -y libcairo2-dev
RUN apt-get install -y libpango1.0-dev
RUN python -m pip install --upgrade pip
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /app
COPY ./tmp /tmp

