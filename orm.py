import logging

import aiomysql

logging.basicConfig(level=logging.INFO)


async def create_pool(loop=None, **kwargs):
    logging.info('create database connect pool...')
    global __pool
    __pool = await aiomysql.create_pool(
        host=kwargs.get('host', 'localhost'),
        port=kwargs.get('port', 3306),
        user=kwargs.get('user'),
        password=kwargs.get('password'),
        db=kwargs.get('db'),
        charset=kwargs.get('charset', 'utf8'),
        autocommit=kwargs.get('autocommit', True),
        maxsize=kwargs.get('maxsize', 10),
        minsize=kwargs.get('minsize', 1),
        loop=loop
    )


async def select(sql, args, size=None):
    logging.info(sql, args)
    with (await __pool) as conn:
        cur = await conn.cursor(aiomysql.DictCursor)
        await cur.execute(sql.replace('?', '%s'), args or ())
        if size:
            rs = await cur.fetchmany(size)
        else:
            rs = await cur.fetchall()
        await cur.close()
        logging.info('rows returned:%s' % len(rs))

        return rs


async def execute(sql, args):
    logging.info(sql)
    logging.info(args)
    with (await __pool) as conn:
        try:
            cur = await conn.cursor(aiomysql.DictCursor)
            await cur.execute(sql.replace('?', '%s'), args or ())
            affected = cur.rowcount
            await cur.close()
        except Exception as e:
            raise
        return affected


class Field(object):
    def __init__(self, name, column_type, default, primary_key):
        self.name = name
        self.column_type = column_type
        self.default = default
        self.primary_key = primary_key

    def __str__(self):
        return '<%s,%s:%s,%s>' % (self.__class__.__name__, self.column_type, self.name, self.default)


class StringField(Field):
    def __init__(self, name=None, ddl='varchar(100)', default=None, primary_key=False):
        super().__init__(name, ddl, default, primary_key)


class TextField(Field):
    def __init__(self, name=None, ddl='text', default=None, primary_key=False):
        super().__init__(name, ddl, default, primary_key)


class IntegerField(Field):
    def __init__(self, name=None, ddl='int', default=None, primary_key=True):
        super().__init__(name, ddl, default, primary_key)


class FloatField(Field):
    def __init__(self, name=None, ddl='real', default=None, primary_key=False):
        super().__init__(name, ddl, default, primary_key)


class BooleanField(Field):
    def __init__(self, name=None, ddl='boolean', default=False, primary_key=False):
        super().__init__(name, ddl, default, primary_key)


# field = StringField('name', 'varchar(100)', 'zhangsan', False)
# print(field)




def create_args_string(param):
    L = []
    for n in range(param):
        L.append('?')
    return ', '.join(L)


class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        if name == 'Model':
            return type.__new__(cls, name, bases, attrs)

        tableName = attrs.get('__table__', None) or name
        logging.info('found model:%s (table:%s)' % (name, tableName))

        mappings = dict()
        fields = []
        primaryKey = None

        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('found mapping:%s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field:%s' % k)
                    primaryKey = k
                else:
                    fields.append(k)

        if not primaryKey:
            raise RuntimeError('primary key not found.')

        for k in mappings.keys():
            attrs.pop(k)

        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        attrs['__mappings__'] = mappings
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey
        attrs['__fields__'] = fields
        attrs['__select__'] = 'select `%s`,%s from `%s`' % (primaryKey, ','.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s`(`%s`,%s) values(%s)' % (
            tableName, primaryKey, ','.join(escaped_fields), create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (
            tableName, ','.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` whre `%s`=?' % (tableName, primaryKey)
        attrs[
            '__sql__'] = 'create table `%s`(%s,%s,key `idx_create_at`(`create_at`),PRIMARY KEY (`id`)) engine=innodb default charset=utf8' % (
            tableName, '`%s` %s not null' % (primaryKey, mappings.get(primaryKey).column_type),
            ','.join(
                map(lambda f: '`%s` %s not null' % (mappings.get(f).name or f, mappings.get(f).column_type), fields)))

        return type.__new__(cls, name, bases, attrs)


class Model(dict, metaclass=ModelMetaclass):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)

        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s:%s' % (key, str(value)))
                setattr(self, key, value)
        return value

    @classmethod
    def sql(cls):
        return cls.__sql__

    @classmethod
    async def find(cls, pk):
        'find object by primary key'
        rs = await select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        else:
            return cls(**rs[0])

    async def save(self):
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.insert(0, self.getValueOrDefault(self.__primary_key__))
        rows = await execute(self.__insert__, args)
        if rows != 1:
            logging.warning('failed to insert record:affected rows:%s' % rows)
