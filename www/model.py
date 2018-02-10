import uuid
from time import time

from www.orm import Model, StringField, BooleanField, FloatField, TextField


def nextId():
    return '%015d%s000' % (int(time()), uuid.uuid4().hex)


# model = Model()
# model['name'] = 'test'
# print(model['name'])
# print(model.name)


class User(Model):
    __table__ = 'users'

    id = StringField(primary_key=True, default=nextId, ddl='varchar(50)')
    email = StringField(ddl='varchar(50)')
    passwd = StringField(ddl='varchar(50)')
    admin = BooleanField()
    name = StringField(ddl='varchar(50)')
    image = StringField(ddl='varchar(500)')
    create_at = FloatField(default=time)


class Blog(Model):
    __table__ = 'blogs'

    id = StringField(primary_key=True, default=nextId, ddl='varchar(50)')

    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    name = StringField(ddl='varchar(50)')
    summary = StringField(ddl='varchar(200)')
    content = TextField()
    create_at = FloatField(default=time)


class Comment(Model):
    __table__ = 'comments'

    id = StringField(primary_key=True, default=nextId, ddl='varchar(50)')

    blog_id = StringField(ddl='varchar(50)')
    user_id = StringField(ddl='varchar(50)')
    user_name = StringField(ddl='varchar(50)')
    user_image = StringField(ddl='varchar(500)')
    content = TextField()
    create_at = FloatField(default=time)


# print(User.sql())
# print(Blog.sql())
# print(Comment.sql())


# async def test(loop):
#     await orm.create_pool(loop=loop, user='blog', password='blog', db='blog')
#     user = User(name='test', email='test@example.com', passwd='test', image='about:blank')
#     await user.save()
#
#
# loop = asyncio.get_event_loop()
# loop.run_until_complete(test(loop))
# loop.run_forever()


# create table `users`(`email` varchar(50) not null,`passwd` varchar(50) not null,`admin` boolean not null,`name` varchar(50) not null,`image` varchar(500) not null,`create_at` real not null,key `idx_create_at`(`create at`),PRIMARY KEY (`id`) engine=innodb defalut charset=utf8)

# user.insert()
# users = User.findAll()
