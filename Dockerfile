FROM --platform=linux/amd64 python:3.9

ENV DEBIAN_FRONTEND=noninteractive
ENV LC_ALL=en_US.UTF-8

RUN apt-get update \
  && apt-get install -y tzdata \
  && pip3 install --upgrade pip

# Upgrade pip
RUN python -m pip install --upgrade pip

RUN echo "Asia/Singapore" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata
ENV TZ Asia/Singapore

RUN mkdir /app
RUN mkdir /app/db
RUN mkdir /app/logs

WORKDIR /app
COPY . /app

RUN pip install poetry
RUN poetry install --no-root
RUN poetry env use python
RUN poetry run alembic upgrade head
RUN ["chmod", "a+x", "./bin/run.sh"]
EXPOSE 5555

CMD ["sh", "-c", "/app/bin/run.sh start"]
