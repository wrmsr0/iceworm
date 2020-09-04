# flake8: noqa
# protoc: libprotoc 3.13.0
# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: iceworm.proto
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='iceworm.proto',
  package='iceworm',
  syntax='proto3',
  serialized_options=b'\n\021com.wrmsr.iceworm',
  create_key=_descriptor._internal_create_key,
  serialized_pb=b'\n\riceworm.proto\x12\x07iceworm\"\"\n\x10WebServiceStatus\x12\x0e\n\x06uptime\x18\x01 \x01(\x02\"\x15\n\x05_Stub\x12\x0c\n\x04\x64\x61ta\x18\x01 \x01(\tB\x13\n\x11\x63om.wrmsr.icewormb\x06proto3'
)




_WEBSERVICESTATUS = _descriptor.Descriptor(
  name='WebServiceStatus',
  full_name='iceworm.WebServiceStatus',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='uptime', full_name='iceworm.WebServiceStatus.uptime', index=0,
      number=1, type=2, cpp_type=6, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=26,
  serialized_end=60,
)


__STUB = _descriptor.Descriptor(
  name='_Stub',
  full_name='iceworm._Stub',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  create_key=_descriptor._internal_create_key,
  fields=[
    _descriptor.FieldDescriptor(
      name='data', full_name='iceworm._Stub.data', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=b"".decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR,  create_key=_descriptor._internal_create_key),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=62,
  serialized_end=83,
)

DESCRIPTOR.message_types_by_name['WebServiceStatus'] = _WEBSERVICESTATUS
DESCRIPTOR.message_types_by_name['_Stub'] = __STUB
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

WebServiceStatus = _reflection.GeneratedProtocolMessageType('WebServiceStatus', (_message.Message,), {
  'DESCRIPTOR' : _WEBSERVICESTATUS,
  '__module__' : 'iceworm_pb2'
  # @@protoc_insertion_point(class_scope:iceworm.WebServiceStatus)
  })
_sym_db.RegisterMessage(WebServiceStatus)

_Stub = _reflection.GeneratedProtocolMessageType('_Stub', (_message.Message,), {
  'DESCRIPTOR' : __STUB,
  '__module__' : 'iceworm_pb2'
  # @@protoc_insertion_point(class_scope:iceworm._Stub)
  })
_sym_db.RegisterMessage(_Stub)


DESCRIPTOR._options = None
# @@protoc_insertion_point(module_scope)
