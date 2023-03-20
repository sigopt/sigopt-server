# Copyright © 2022 Intel Corporation
#
# SPDX-License-Identifier: Apache License 2.0
# from sqlalchemy import BigInteger, Column, ForeignKey, ForeignKeyConstraint, Index, String, UniqueConstraint
# from sqlalchemy.orm import validates

# from zigopt.common import *
# from zigopt.db.column import ProtobufColumn, ProtobufColumnValidator
# from zigopt.protobuf.gen.web_data.run_view_pb2 import Filter, RunViewData, Sort
# from zigopt.project.model import MAX_ID_LENGTH
# from zigopt.web_data.model import WebDataBase


# MAX_DISPLAY_NAME_LENGTH = 100

# class RunView(WebDataBase):
#   __tablename__ = 'run_view'
#   id = Column(
#     BigInteger,
#     ForeignKey('web_data.id', ondelete='CASCADE', name='run_view_web_data_id_fkey'),
#     primary_key=True,
#   )
#   client_id = Column(BigInteger, nullable=False)
#   project_reference_id = Column(String(MAX_ID_LENGTH), nullable=False)
#   display_name = Column(String(MAX_DISPLAY_NAME_LENGTH))
#   data = ProtobufColumn(RunViewData)

#   __table_args__ = (
#     ForeignKeyConstraint(
#       ['client_id', 'project_reference_id'],
#       ['projects.client_id', 'projects.reference_id'],
#       ondelete='CASCADE',
#       name='run_view_projects_fkey',
#     ),
#     Index('client_id', 'project_reference_id'),
#     UniqueConstraint('client_id', 'project_reference_id', 'display_name'),
#   )

#   def __init__(self, *args, **kwargs):
#     super().__init__(*args, **kwargs)

#   @validates('data')
#   def validator(self, key, meta):
#     return ProtobufColumnValidator(meta)

# def filter_json_to_proto(f):
#   filter_proto = Filter(
#     enabled=f['enabled'],
#     field=f['field'],
#     operator=f['operator'],
#   )
#   if(is_number(f['value'])):
#     filter_proto.numeric_value = f['value']
#   else:
#     filter_proto.string_value = f['value']
#   return filter_proto

# def sort_json_to_proto(sort):
#   return Sort(key=sort['key'], ascending=sort['ascending'])

# def run_view_json_to_proto(view_json):
#   new_view = RunViewData(
#     filters=[filter_json_to_proto(_filter) for _filter in view_json['filters']],
#     sort=[sort_json_to_proto(sort) for sort in view_json['sort']],
#     column_state=view_json.get('column_state', '')
#   )

#   return new_view

# def payload_to_run_view(parent_resource_id, created_by, payload):
#   return RunView(
#     client_id=int(parent_resource_id['client']),
#     created_by=created_by,
#     data=run_view_json_to_proto(payload['view']),
#     display_name=payload['display_name'],
#     # project.id we return to client is project.reference_id in database
#     project_reference_id=parent_resource_id['project'],
#   )
