from flask_restx import Namespace, Resource, fields
from flask_security import auth_required

tags_ns = Namespace("tags", description="Tag management")

_tag_model = tags_ns.model("Tag", {
    "id": fields.String(description="Tag UUID"),
    "name": fields.String(description="Tag name"),
})

_tag_list_model = tags_ns.model("TagList", {
    "tags": fields.List(fields.Nested(_tag_model)),
})

_add_tags_model = tags_ns.model("AddTagsRequest", {
    "tags": fields.List(fields.String, required=True, description='List of tag name strings, e.g. ["ml", "nlp"]'),
})

_patch_tag_model = tags_ns.model("PatchTagRequest", {
    "accepted": fields.Boolean(required=True, description="Set to true to accept, false to reject"),
})


@tags_ns.route("")
class TagList(Resource):
    @auth_required()
    @tags_ns.marshal_with(_tag_list_model, code=200)
    @tags_ns.doc(
        security="apikey",
        responses={200: "OK", 401: "Unauthorized"},
    )
    def get(self):
        """List all tags in the system — implemented in task 9.1."""
        pass


@tags_ns.route("/<doc_id>/tags", doc={"description": "Add tags to a document"})
class DocumentTags(Resource):
    @auth_required()
    @tags_ns.expect(_add_tags_model)
    @tags_ns.doc(
        security="apikey",
        params={"doc_id": "Document UUID"},
        responses={200: "Tags added", 401: "Unauthorized", 404: "Document not found"},
    )
    def post(self, doc_id):
        """Add tags to a document (creates or reuses existing tags) — implemented in task 9.2."""
        pass


@tags_ns.route("/<doc_id>/tags/<tag_id>")
class DocumentTagDetail(Resource):
    @auth_required()
    @tags_ns.expect(_patch_tag_model)
    @tags_ns.doc(
        security="apikey",
        params={"doc_id": "Document UUID", "tag_id": "Tag UUID"},
        responses={200: "Updated", 401: "Unauthorized", 404: "Not found"},
    )
    def patch(self, doc_id, tag_id):
        """Accept or reject a tag on a document — implemented in task 9.3."""
        pass
