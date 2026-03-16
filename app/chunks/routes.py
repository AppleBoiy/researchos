from flask_restx import Namespace, Resource
from flask_security import auth_required

chunks_ns = Namespace("chunks", description="Chunked file upload")

_chunk_parser = chunks_ns.parser()
_chunk_parser.add_argument(
    "X-Chunk-Index", location="headers", type=int, required=True,
    help="Zero-based index of this chunk",
)
_chunk_parser.add_argument(
    "X-Total-Chunks", location="headers", type=int, required=True,
    help="Total number of chunks for this upload",
)
_chunk_parser.add_argument(
    "body", location="data", required=True,
    help="Raw binary chunk data (max 10 MB)",
)


@chunks_ns.route("/<doc_id>/chunks")
class ChunkUpload(Resource):
    @auth_required()
    @chunks_ns.expect(_chunk_parser)
    @chunks_ns.doc(
        security="apikey",
        params={"doc_id": "Document UUID"},
        responses={
            200: "Chunk stored, returns progress",
            400: "Missing or invalid headers",
            401: "Unauthorized",
            413: "Chunk exceeds 10 MB",
        },
    )
    def post(self, doc_id):
        """Upload a single chunk — implemented in task 6.1."""
        pass
