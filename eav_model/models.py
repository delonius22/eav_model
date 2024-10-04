from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.ext.associationproxy import association_proxy

db = SQLAlchemy()


class Entity(db.Model):
  def __init__(self, description, values = None):
    self.description = description
    if values is None:
      values = {}
    for name, value in values.items():
      self.values[name] = value

  id = db.Column(db.Integer, primary_key=True, autoincrement=True)

  description = db.Column(db.String)

  # Attribute values as list
  #
  # Values are lazy loaded, for performance subquery can be used:
  #
  #   Entity.query.options(
  #     db.subqueryload('attribute_values')
  #   ).all()
  # 
  # Values are also exposed as dictionary in attributes, given by attribute name
  #
  attribute_values = db.relationship('Value', 
    collection_class=attribute_mapped_collection('_attribute_name'))

  # Attributes values as dictionary by attribute name
  #
  #    e = Entity('hello')
  #    e.attributes['origin'] = 'Earth'
  #
  #    print(e.attributes)
  #    >> {u'origin': u'Earth'}
  #
  attributes = association_proxy('attribute_values', 'value', 
    creator=lambda k, v: Value(k,v))


class Attribute(db.Model):
  def __init__(self, name):
    self.name = name
  
  @classmethod
  def get_or_create(cls, name, *arg, **kw):
    with db.session.no_autoflush:
      q = cls.query.filter_by(name=name)
      obj = q.first()
      if not obj:
        obj = cls(name, *arg, **kw)
        db.session.add(obj)
    return obj
    
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  
  # Unique attribute name so it can be used as dictionary key
  name = db.Column(db.String(100), nullable=False, unique=True)


class Value(db.Model):
  __table_args__ = (
    db.UniqueConstraint('entity_id', 'attribute_id'),
  )

  def __init__(self, attribute_name, value):
    self._attribute_name = attribute_name
    self.value = value
  
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)

  entity_id = db.Column(db.Integer, db.ForeignKey('entity.id'), nullable=False)

  attribute_id = db.Column(db.Integer, db.ForeignKey('attribute.id'), nullable=False)

  # Value string
  value = db.Column(db.String)

  # Relationship to use in association proxy
  _attribute = db.relationship('Attribute', uselist=False, 
    foreign_keys=[attribute_id], lazy='joined')

  # Expose attribute name as proxy
  _attribute_name = association_proxy('_attribute', 'name', 
    creator=lambda v: Attribute.get_or_create(v))


def init_db():
	db.create_all()