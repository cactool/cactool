FROM python:3.10-bullseye
WORKDIR /source
COPY . .
RUN python -m pip install .
WORKDIR /instance
EXPOSE 8000
CMD ["cactool"]
