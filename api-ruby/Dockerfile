FROM ruby:3.0
WORKDIR /app
COPY Gemfile .
RUN bundle install
COPY main.rb .
EXPOSE 4567
CMD ["ruby", "main.rb"]
