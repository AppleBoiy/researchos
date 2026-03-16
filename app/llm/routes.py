from flask_restx import Namespace, Resource, fields
from flask_security import auth_required

llm_ns = Namespace("llm", description="LLM auto-tagging")

_autotag_response_model = llm_ns.model("AutoTagResponse", {
    "tags": fields.List(fields.String, description="5 suggested tag names"),
})


@llm_ns.route("/<doc_id>/autotag")
class AutoTag(Resource):
    @auth_required()
    @llm_ns.marshal_with(_autotag_response_model, code=200)
    @llm_ns.doc(
        security="apikey",
        params={"doc_id": "Document UUID"},
        responses={
            200: "5 tag suggestions stored with accepted=false",
            401: "Unauthorized",
            404: "Document not found",
            422: "Document is not a PDF",
            502: "LLM API error or timeout",
        },
    )
    def post(self, doc_id):
        """Auto-tag a PDF document using LLM — implemented in task 10.3."""
        pass
