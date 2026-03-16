from flask_restx import Namespace, Resource, fields
from flask_security import auth_required

transfers_ns = Namespace("transfers", description="File transfer jobs")

_source_model = transfers_ns.model("TransferSource", {
    "type": fields.String(required=True, description="ssh or s3 or local", example="ssh"),
    "host": fields.String(description="Remote hostname or IP"),
    "port": fields.Integer(description="SSH port", example=22),
    "username": fields.String(description="SSH username"),
    "key_path": fields.String(description="Path to private key file"),
    "path": fields.String(description="Remote file path to pull"),
})

_dest_model = transfers_ns.model("TransferDestination", {
    "type": fields.String(required=True, description="ssh or s3 or local", example="s3"),
    "host": fields.String(description="Remote hostname (SSH only)"),
    "port": fields.Integer(description="SSH port (SSH only)", example=22),
    "username": fields.String(description="SSH username (SSH only)"),
    "key_path": fields.String(description="Path to private key file (SSH only)"),
    "path": fields.String(description="Remote destination path (SSH only)"),
    "bucket": fields.String(description="S3 bucket name (S3 only)"),
    "prefix": fields.String(description="S3 object key prefix (S3 only)"),
})

_transfer_request_model = transfers_ns.model("TransferRequest", {
    "document_id": fields.String(required=True, description="UUID of the document to transfer"),
    "source": fields.Nested(_source_model, required=True),
    "destination": fields.Nested(_dest_model, required=True),
})

_transfer_response_model = transfers_ns.model("TransferJob", {
    "id": fields.String(description="TransferJob UUID"),
    "document_id": fields.String(description="Document UUID"),
    "status": fields.String(description="pending | in_progress | completed | failed"),
    "source": fields.Nested(_source_model),
    "destination": fields.Nested(_dest_model),
    "error_message": fields.String(description="Error detail if failed"),
    "created_at": fields.String(description="ISO8601 timestamp"),
    "updated_at": fields.String(description="ISO8601 timestamp"),
})


@transfers_ns.route("")
class TransferList(Resource):
    @auth_required()
    @transfers_ns.expect(_transfer_request_model)
    @transfers_ns.doc(
        security="apikey",
        responses={202: "Accepted — transfer started", 400: "Bad request", 401: "Unauthorized"},
    )
    def post(self):
        """Create a transfer job (returns 202 immediately) — implemented in task 7.3."""
        pass


@transfers_ns.route("/<job_id>")
class TransferDetail(Resource):
    @auth_required()
    @transfers_ns.marshal_with(_transfer_response_model, code=200)
    @transfers_ns.doc(
        security="apikey",
        params={"job_id": "TransferJob UUID"},
        responses={200: "OK", 401: "Unauthorized", 404: "Not found"},
    )
    def get(self, job_id):
        """Get transfer job status — implemented in task 7.4."""
        pass
