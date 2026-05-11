require 'sinatra'
require 'nokogiri'
require 'httparty'
require 'redis'
require 'json'

set :bind, '0.0.0.0'
set :port, 4567
set :protection, :except => [:host_authorization]

REDIS_HOST = ENV['REDIS_HOST'] || 'redis'
REDIS_PORT = ENV['REDIS_PORT'] || 6379
ENABLE_CACHE = ENV['ENABLE_CACHE'] != 'false'

if ENABLE_CACHE
  $cache = Redis.new(host: REDIS_HOST, port: REDIS_PORT)
end

get '/api/extract' do
  content_type :json
  url = params['url']
  return { error: 'No URL provided' }.to_json if url.nil? || url.empty?

  # Try cache
  if ENABLE_CACHE && $cache
    cached_data = $cache.get(url)
    return cached_data if cached_data
  end

  # Extract
  begin
    response = HTTParty.get(url)
    doc = Nokogiri::HTML(response.body)
    links = []
    doc.css('a').each do |link|
      href = link['href']
      links << { text: link.text.strip, href: href } if href
    end

    result = { url: url, links: links }.to_json

    # Store in cache
    if ENABLE_CACHE && $cache
      $cache.set(url, result)
    end

    return result
  rescue => e
    status 500
    { error: e.message }.to_json
  end
end
