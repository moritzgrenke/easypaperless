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


## general features

client.documents.list(): archive_serial_number => null => filter for archive_serial_number__isnull=TRUE

documents.bulk_modify_tags(): test edge case of mixed int/str param "add_tags". 

tags.create() - can't find param "parent" in the api. later version of paperless-ngx?

logging needs to be added.

custom_fields.update(): param "extra_data" needs attention: -> typing.Any, vague documentation of the format.


after issue 0019 was implemented: I'm not sure if UNSET is necessary for the documents.upload method.


enable configuration: what are the defaults? - perhaps a mcp server topic!?


###
in correspondents.create(), document_types.create() and storage_paths.create() and tags.create() -> parameter "is_insensitive" is None by default. this means the parameter is omitted. the api default is "true" afik. i think it is better to set the default to "true" instead of None. so that the user is aware of the actual behaviour. doesn't apply to the update() methods because there "None" means - don't change it. Thats ok.


## 16.03.


check again: documents.get_metadata() - working?


Out of scope: paperless-ngx error? created should be nullable?

client poll_intervall and poll_timeout : docstring has hint "in seconds"?


bulk_set_permissions in documents lead to an error 500 (when tested via the mcp server).






