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



## general features

client.documents.list(): archive_serial_number => null => filter for archive_serial_number__isnull=TRUE

documents.bulk_modify_tags(): test edge case of mixed int/str param "add_tags". 

tags.create() - can't find param "parent" in the api. later version of paperless-ngx?
passing non existing parameters doesn't lead to an error (i had this once with a misspelled param.) leads to the situation that if api wrapper expects a later version of the api, but param doesn't yet exist, the param is silently ignored. give some kind of warning? e.g. query the version when initializing the client then check again a list of params - throw exceptions if param used that isn't available in the detected version!?

logging needs to be added.

custom_fields.update(): param "extra_data" needs attention: -> typing.Any, vague documentation of the format.


after issue 0019 was implemented: I'm not sure if UNSET is necessary for the documents.upload method.


enable configuration: what are the defaults? - perhaps a mcp server topic!?


###
in correspondents.create(), document_types.create() and storage_paths.create() and tags.create() -> parameter "is_insensitive" is None by default. this means the parameter is omitted. the api default is "true" afik. i think it is better to set the default to "true" instead of None. so that the user is aware of the actual behaviour. doesn't apply to the update() methods because there "None" means - don't change it. Thats ok.


## 16.03.


Out of scope: paperless-ngx error? created should be nullable?

bulk_set_permissions in documents lead to an error 500 (when tested via the mcp server and both params none).



## 20.03.

planning to add more resources:
v0.4.0: permission project: profile, trash, users
v0.5.0: admin suite: config, groups, logs, saved_views, status, tasks?, token?, ui_settings
v0.6.0: rest: documents.*, mail_accounts, mail_rules, oauth?, remote_version?, search?, share_links, statistics, workflow_actions, workflow_triggers, workflows