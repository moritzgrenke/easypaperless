# Notes Claude / Development Process

development process writes tests!?

## tests
tests gaps: 
parameters with multiple types: add multiple tests (at least one per type). e.g. list_documents with parameter modified_after 
nonsense values: list_documents with checksum="hello world" => delivered a full return list, because api parameter was wrong (and then ignored)



looks like: upload_document has no custom fields, upload document has no owner field?!



todo: test the https:// connection to my live instance.

## documentation
refer in parameters "matching_algorithm" to the class MatchingAlgorithm: e.g. storage_paths.create(), tags.create()
date filter in documents.list(): say something about the iso format!?
documents.list(): custom_field_query - format? examples?

documents.upload(): poll_interval, poll_timeout in seconds?

documents.bulk_edit(): add remark again "better use high-level methods", add full list of implemented methods. say explicitly that not all methods were implemented.

## parameter completeness:
correspondents: 
    missing fields in update(): "owner", "set_permissions"
custom_fields: 
    missing fields in list(): "name_contains", "name_exact"
    missing in update(): "data_type
document_types:
    missing fields in update(): "owner", "set_permissions"
documents
    missing fields in list(): "document_type_name_exact", "document_type_name_contains"
    missing fields in update(): "remove_inbox_tags"
    upload(): "custom_fields"
storage_paths
    missing fields in list(): "path_exact", "path_contains"
    missing fields in update(): "owner", "set_permissions" (available in the user interface - not shown in api documentation)
tags
    missing fields in update(): "owner", "set_permissions"

## general features
in correspondents.create() and storage_paths.create() and tags.create() -> parameter "is_insensitive" is None by default. this means the parameter is omitted. the api default is "true". i think it is better to set the default to "true" instead of None. so that the user is aware of the actual behaviour. doesn't apply to the update() methods because there "None" means - don't change it. Thats ok.
client.documents.list(): archive_serial_number => null => filter for archive_serial_number__isnull=TRUE

check: archive_serial_number sometimes abbreviated as asn? here: documents.update(), documents.upload()
in documents.update() parameter is called date. should be called "created" 
search_mde should be "title_or_text" but "title_or_content" - stick to the name of field "content"!

documents.upload(): created should accept either date or str. currently only string.

documents.bulk_modify_tags(): test edge case of mixed int/str param "add_tags". 

tags.create() - can't find param "parent" in the api. later version of paperless-ngx?

logging needs to be added.

custom_fields.update(): param "extra_data" needs attention: -> typing.Any, vague documentation of the format.

### None Topic
update document: owner = None should be forwarded to the api as owner = null => deleting owner!
solve with pydantic

