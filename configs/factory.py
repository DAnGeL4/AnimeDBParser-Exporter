#--Start imports block
#System imports
import dataclasses as dcls

#Custom imports
#--Finish imports block


#--Start global constants block
#--Finish global constants block


#--Start functional block
def _build_dataclass_type(name, fields, namespace):
    dataclass_type = dcls.make_dataclass(name, fields, namespace=namespace)
    return dataclass_type

def _build_processed_titles_dump_namespace():
    namespace={'asdict': lambda self: 
               {k: v for k, v in dcls.asdict(self).items()}}
    return namespace

def _build_processed_titles_dump_fields(fields_type, fields_container):
    fields = list([(wlist.value, fields_type, 
                    dcls.field(default_factory=dict)) 
                   for wlist in fields_container])
    fields.append(('errors', fields_type, 
                   dcls.field(default_factory=dict)))
    return fields

def build_processed_titles_dump_type(fields_type, fields_container):
    name = 'ProcessedTitlesDump'
    fields = _build_processed_titles_dump_fields(fields_type, fields_container)
    namespace = _build_processed_titles_dump_namespace()
    
    dataclass_type = _build_dataclass_type(name, fields, namespace)
    return dataclass_type

#--Finish functional block