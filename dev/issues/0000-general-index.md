# Feature Index

**Next Available ID:** 0040

| ID | Type | Name | Status | File |
|----|------|------|--------|------|
| 0001 | Feature | HTTP Client Core | Deployed | [0001-http-client-core.md](0001-http-client-core.md) |
| 0002 | Feature | Name-to-ID Resolver | Deployed | [0002-name-to-id-resolver.md](0002-name-to-id-resolver.md) |
| 0003 | Feature | Document List with Filters | Deployed | [0003-list-documents.md](0003-list-documents.md) |
| 0004 | Feature | Get Document by ID | Deployed | [0004-get-document.md](0004-get-document.md) |
| 0005 | Feature | Update Document | Deployed | [0005-update-document.md](0005-update-document.md) |
| 0006 | Feature | Delete Document | Deployed | [0006-delete-document.md](0006-delete-document.md) |
| 0007 | Feature | Download Document | Deployed | [0007-download-document.md](0007-download-document.md) |
| 0008 | Feature | Upload Document | Deployed | [0008-upload-document.md](0008-upload-document.md) |
| 0009 | Feature | Document Bulk Operations | Deployed | [0009-document-bulk-operations.md](0009-document-bulk-operations.md) |
| 0010 | Feature | Tags CRUD | Deployed | [0010-tags-crud.md](0010-tags-crud.md) |
| 0011 | Feature | Correspondents CRUD | Deployed | [0011-correspondents-crud.md](0011-correspondents-crud.md) |
| 0012 | Feature | Document Types CRUD | Deployed | [0012-document-types-crud.md](0012-document-types-crud.md) |
| 0013 | Feature | Custom Fields CRUD | Deployed | [0013-custom-fields-crud.md](0013-custom-fields-crud.md) |
| 0014 | Feature | Storage Paths CRUD | Deployed | [0014-storage-paths-crud.md](0014-storage-paths-crud.md) |
| 0015 | Feature | Non-Document Bulk Operations | Deployed | [0015-non-document-bulk-operations.md](0015-non-document-bulk-operations.md) |
| 0016 | Feature | SyncPaperlessClient | Deployed | [0016-sync-client.md](0016-sync-client.md) |
| 0017 | Feature | Document Notes | Deployed | [0017-document-notes.md](0017-document-notes.md) |
| 0018 | Refactoring | Resource-Based Client API | Deployed | [018-refactoring-resource_based_client_api.md](018-refactoring-resource_based_client_api.md) |
| 0019 | Bug | None Cannot Express Explicit Null in Update/List Methods | Deployed | [0019-bug-update_document_nullable_fields_unresettable.md](0019-bug-update_document_nullable_fields_unresettable.md) |
| 0020 | Task | Complete Missing Resource Parameters | Deployed | [0020-task-complete_missing_resource_parameters.md](0020-task-complete_missing_resource_parameters.md) |
| 0021 | Bug | Documents Resource API Inconsistencies | Deployed | [0021-bug-documents_resource_api_inconsistencies.md](0021-bug-documents_resource_api_inconsistencies.md) |
| 0022 | Bug | `is_insensitive` Misleading Default in `create()` Methods | Deployed | [0022-bug-is_insensitive_misleading_default_in_create.md](0022-bug-is_insensitive_misleading_default_in_create.md) |
| 0023 | Refactoring | Hide Low-Level Bulk Edit Methods from Public API | Deployed | [0023-refactoring-hide_low_level_bulk_edit_methods.md](0023-refactoring-hide_low_level_bulk_edit_methods.md) |
| 0024 | Maintenance | Add py.typed Marker File for PEP 561 Compliance | Deployed | [0024-maintenance-add_py_typed_marker.md](0024-maintenance-add_py_typed_marker.md) |
| 0025 | Bug | `Document.created` Typed as `datetime` Instead of `date` | Deployed | [0025-bug-document_created_field_wrong_type.md](0025-bug-document_created_field_wrong_type.md) |
| 0026 | Refactoring | Expand Sync Method Docstrings with Full Parameter Documentation | Deployed | [0026-refactoring-sync_docstrings_full_param_docs.md](0026-refactoring-sync_docstrings_full_param_docs.md) |
| 0027 | Bug | `SyncTagsResource.create()` Wrong Default Values for `color` and `is_inbox_tag` | Deployed | [0027-bug-sync_tags_create_wrong_default_values.md](0027-bug-sync_tags_create_wrong_default_values.md) |
| 0028 | Refactoring | Fix None/Unset Semantics Across Async Resource Methods and Expose Public `Unset` Alias | Deployed | [0028-refactoring-fix_none_unset_semantics_and_public_unset_alias.md](0028-refactoring-fix_none_unset_semantics_and_public_unset_alias.md) |
| 0029 | Feature | Return PagedResult Model from All list() Methods | Deployed | [0029-feature-paged_result_model_for_list_methods.md](0029-feature-paged_result_model_for_list_methods.md) |
| 0030 | Feature | Add Structured Logging Support Across All Resource Methods | Deployed | [0030-feature-structured_logging_support.md](0030-feature-structured_logging_support.md) |
| 0031 | Refactoring | Rename `api_key` Parameter to `api_token` in Clients and Scripts | Deployed | [0031-refactoring-rename_api_key_to_api_token.md](0031-refactoring-rename_api_key_to_api_token.md) |
| 0032 | Bug | `documents.notes.list()` Does Not Return `PagedResult` | Deployed | [0032-bug-notes_list_missing_paged_result.md](0032-bug-notes_list_missing_paged_result.md) |
| 0033 | Bug | Pagination Follows Wrong Scheme on HTTPS Instances Behind Reverse Proxy | Deployed | [0033-bug-pagination_wrong_scheme_on_https.md](0033-bug-pagination_wrong_scheme_on_https.md) |
| 0034 | Bug | `notes.list()` Crashes at Runtime with AttributeError on Real Instance | Deployed | [0034-bug-notes_list_crashes_on_plain_array_response.md](0034-bug-notes_list_crashes_on_plain_array_response.md) |
| 0035 | Feature | Users Resource CRUD | Deployed | [0035-feature-users_resource_crud.md](0035-feature-users_resource_crud.md) |
| 0036 | Feature | Trash Resource | Deployed | [0036-feature-trash_resource.md](0036-feature-trash_resource.md) |
| 0037 | Bug | `documents.download(original=True)` Returns Archived PDF Instead of Original File | Deployed | [0037-bug-download_original_returns_pdf.md](0037-bug-download_original_returns_pdf.md) |
| 0038 | Feature | Document Thumbnail | Deployed | [0038-feature-document_thumbnail.md](0038-feature-document_thumbnail.md) |
| 0039 | Feature | Document Bulk Download | Deployed | [0039-feature-document_bulk_download.md](0039-feature-document_bulk_download.md) |
