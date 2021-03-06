from aiohttp import web
import pathlib
import bson
import json
import datetime
import httpagentparser

from blogapi import util

DATA_DIR = pathlib.Path(__file__).parent.parent / 'data'
with open(DATA_DIR / 'countries.json') as fh:
  COUNTRY_DATA = json.load(fh)
with open(DATA_DIR / 'timezones.json') as fh:
  TIMEZONE_DATA = json.load(fh)

schema_template = {
  'browser': {
    'name': str,
    'version': str
  },
  'datetime': str,
  'os': str,
  'path': str,
  'platform': str,
  'referrer': str,
  'screen': {
    'width': int,
    'height': int,
    'orientation': str,
  },
  'sources': {
    '*': str,
  },
  'timezone': str,
  'userAgent': str
}


def check_data(data, schema):
  for key in data:
    schema_key = '*' if '*' in schema else key

    if key not in schema:
      raise web.HTTPBadRequest()
    elif type(schema[schema_key]) == dict:
      check_data(data[key], schema[schema_key])
    elif data[key] is not None and type(data[key]) != schema[schema_key]:
      raise web.HTTPBadRequest()
    elif type(data[key]) == str and len(data[key]) > 250:
      raise web.HTTPBadRequest()


async def heartbeat(request):
  data = await request.json()

  check_data(data, schema_template)

  pageview_id = request.headers.get('pageview-id')
  if pageview_id is None:
    return util.json_response({'ok': False})
  db = request.use('db')
  current = db.analytics.find_one({'viewId': bson.ObjectId(pageview_id)})
  if not current:
    return util.json_response({'ok': False})

  path = data['path']
  del data['path']
  update = {'$set': {}}
  for key, value in data.items():
    if value is not None:
      update['$set'][key] = value

  user_id = request.get('user', {}).get('_id', None)
  if user_id:
    update['$set']['isAdmin'] = True

  if not current.get('jsEnabled', False):
    update['$set']['jsEnabled'] = True

  if 'timezone' in data and 'timzone' not in current:
    country_code = TIMEZONE_DATA.get(data['timezone'])
    if country_code:
      data['countryCode'] = country_code
      data['country'] = COUNTRY_DATA.get(country_code, None)
      update['$set']['country'] = data['country']
      update['$set']['countryCode'] = data['countryCode']
      update['$set']['timezone'] = data['timezone']

  paths = current['paths']
  if paths[-1]['url'] != path:
    now = datetime.datetime.utcnow()
    duration = now - paths[-1]['visitedAt']
    update['$set'][f'paths.{len(paths)-1}.length'] = duration.total_seconds()
    update['$set'][f'paths.{len(paths)}'] = {
      'url': path,
      'visitedAt': now
    }

  db.analytics.update_one({'_id': current['_id']}, update)
  return util.json_response({'ok': True, 'viewId': pageview_id})


def create_journey(request):
  path = str(request.path)

  if request.headers.get('user-agent') == 'Node;https://bjornf.dev':
    return None

  referer = request.headers.get('referer', '')
  config = request.app['config']
  unique = True
  if referer.startswith(config['connection.webhost']):
    unique = False

  pageview_id = request.headers.get('pageview-id', str(bson.ObjectId()))
  user_agent = request.headers.get('user-agent')
  parsed = httpagentparser.detect(user_agent)
  os = parsed.get('platform', {}).get('name', None)
  bot = parsed.get('bot', False)
  browser_name = parsed.get('browser', {}).get('name', None)
  browser_version = parsed.get('browser', {}).get('version', '').split('.')[0]

  referer = request.headers.get('Referer')
  sources = {
    key.replace('utm_', ''): value for key, value in request.query.items() if key.startswith('utm_')
  }
  db = request.use('db')

  current = db.analytics.find_one({'viewId': bson.ObjectId(pageview_id)})
  now = datetime.datetime.utcnow()
  if not current:
    current = {
      'createdAt': now,
      'viewId': bson.ObjectId(pageview_id),
      'sources': sources,
      'os': os,
      'paths': [{'url': path, 'visitedAt': now}],
      'isUnique': unique,
      'jsEnabled': False,
      'browser': {
        'name': browser_name,
        'version': browser_version
      },
      'referer': referer,
      'userAgent': user_agent
    }

    if bot:
      current['isProbablyBot'] = True

    db.analytics.insert_one(current)
  return current
