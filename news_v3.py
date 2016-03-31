#encoding:utf-8
import tornado.web,tornado
import motor
from tornado import gen
import redis
#新发布信息页面
class NewMessageHandler(tornado.web.RequestHandler):
	def get(self):
		self.write('''
			<form method="post">
				<input type="text" name="title">
				<input type="text" name="content">
				<input type="submit">
			</form>''')
	
	@gen.coroutine
	def post(self):
		title = self.get_argument('title')
		content = self.get_argument('content')
		db = self.settings['db']
        # insert() returns a Future. Yield the Future to get the result.
		#insert inro redis
		r = self.settings['r']
		msg = 'title:%s content:%s' % (title,content)
		r.lpush('messages3',msg)
		#redis中只保留最新五条信息
		r.ltrim('messages3',0,5)
		result = yield db.messages3.insert({'title': title,'time':'1','content':content})
		# Success
		self.redirect('/')

#首页显示最新6条信息,从redis中获取
class MessagesHandler(tornado.web.RequestHandler):
	@gen.coroutine
	def get(self):
		"""Display all messages."""
		self.write('<a href="/compose">点击发布新的消息</a><br>')
		self.write('<ul>')
		#按发布时间排
		r = self.settings['r']
		titles = r.lrange('messages3',0,-1)
		for title in titles:
			self.write('<li>%s</li>' % title)
		self.write('</ul>')
		self.write('<a href="/next">点击获取历史消息</a><br>')
		self.finish()

#从mongodb中获取旧消息
class NextMessageHandler(tornado.web.RequestHandler):
	@gen.coroutine
	def get(self):
		self.write('<a href="/compose">Compose a message</a><br>')
		self.write('<ul>')
		db = self.settings['db']
		skip_num = 5 
		#不获取缓存中已有的消息
		cursor=db.messages3.find().sort([('_id',-1)]).skip(skip_num)
		#默认按照发布时间排序
		while (yield cursor.fetch_next):
			message = cursor.next_object()
			self.write('<li>title:%s  content:%s</li>' % (message['title'],message['content']))
		self.write('</ul>')
		self.finish()

db = motor.motor_tornado.MotorClient().test
r_redis = redis.Redis(host='localhost') 
#三个页面，依次为发布信息，首页实时信息，历史信息
application = tornado.web.Application(
	[
		(r'/compose', NewMessageHandler),
		(r'/', MessagesHandler),
		(r'/next',NextMessageHandler)
	],
	db=db,
	r = r_redis
)

print('Listening on http://localhost:8888')
application.listen(8888)
tornado.ioloop.IOLoop.instance().start()
