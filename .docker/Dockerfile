# start with official ruby docker image as base
# (bookworm ships python 3.11, the same version the citation workflow uses)
FROM ruby:3.4-bookworm

# set working directory within container
WORKDIR /usr/src/app

# pull in ruby (jekyll) and python (cite process) package info
COPY Gemfile Gemfile.lock _cite/requirements.txt ./

# install ruby packages
RUN VERSION=$(grep -A 1 'BUNDLED WITH' Gemfile.lock | tail -n 1 | xargs); \
    gem install bundler --version ${VERSION} && \
    bundle _${VERSION}_ install

# install python
RUN apt update && apt install -y python3 python3-pip

# install python packages
# (debian marks its python as externally managed; that's fine to override in
# this throwaway container)
RUN python3 -m pip install --no-cache-dir --break-system-packages --upgrade --requirement requirements.txt

# install python package for listening for file changes
RUN python3 -m pip install --no-cache-dir --break-system-packages "watchdog[watchmedo]==3.0.0"

# ports used by jekyll
EXPOSE 4000
EXPOSE 35729

# run jekyll and cite process
COPY .docker/entrypoint.sh /var
CMD [ "/var/entrypoint.sh" ]
