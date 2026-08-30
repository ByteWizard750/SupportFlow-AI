"""
Automated unit tests for SupportFlow AI Phase 3 (RAG Knowledge Base & Suggested Response).

Tests:
1. Knowledge base document ingestion.
2. Document chunking and metadata preservation.
3. Vector store indexing and persistence with FAISS in isolated directory.
4. Semantic retrieval accuracy (verifying expected document matches in top results).
5. Deterministic source attribution.
6. (Optional) Live grounded Gemini response generation when RUN_LIVE_GEMINI=1.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import (
    load_knowledge_base_documents,
    chunk_document,
    build_vector_index,
    retrieve_relevant_chunks,
)
from services.response_service import (
    extract_deterministic_sources,
    generate_suggested_response,
)
from database.database import (
    init_db,
    create_ticket,
    save_suggested_response,
    get_suggested_response,
)
from config import is_gemini_configured


class TestPhase3RAG(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.kb_dir = Path(__file__).resolve().parent / "knowledge_base"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_document_ingestion(self):
        """Test loading all 5 knowledge base documents."""
        docs = load_knowledge_base_documents(kb_dir=self.kb_dir)
        self.assertGreaterEqual(len(docs), 5)
        doc_ids = [d["doc_id"] for d in docs]
        self.assertIn("refund_policy.txt", doc_ids)
        self.assertIn("billing_policy.txt", doc_ids)
        self.assertIn("account_faq.txt", doc_ids)
        self.assertIn("subscription_policy.txt", doc_ids)
        self.assertIn("technical_faq.txt", doc_ids)

    def test_chunking_integrity(self):
        """Test that chunks retain doc_title, section, and non-empty text."""
        docs = load_knowledge_base_documents(kb_dir=self.kb_dir)
        refund_doc = next(d for d in docs if d["doc_id"] == "refund_policy.txt")
        chunks = chunk_document(refund_doc["doc_id"], refund_doc["doc_title"], refund_doc["content"])
        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertEqual(chunk["doc_id"], "refund_policy.txt")
            self.assertIn("doc_title", chunk)
            self.assertIn("section", chunk)
            self.assertGreater(len(chunk["text"]), 10)

    def test_vector_indexing_and_retrieval(self):
        """Test building FAISS index in temp dir and retrieving semantically matching chunks."""
        v_store = self.temp_path / "vector_store"
        index, metadata = build_vector_index(
            kb_dir=self.kb_dir,
            vector_store_dir=v_store,
            force_rebuild=True
        )
        self.assertGreater(index.ntotal, 0)
        self.assertEqual(index.ntotal, len(metadata))

        # Query 1: Refund
        refund_chunks = retrieve_relevant_chunks(
            query="Can I get a refund if I cancel within 14 days?",
            top_k=3,
            kb_dir=self.kb_dir,
            vector_store_dir=v_store
        )
        self.assertGreater(len(refund_chunks), 0)
        doc_titles = [c["doc_title"].lower() for c in refund_chunks]
        self.assertTrue(any("refund" in title for title in doc_titles), "Refund Policy should appear in top results")

        # Query 2: Password Reset / Login
        account_chunks = retrieve_relevant_chunks(
            query="How do I reset my account password after lockout?",
            top_k=3,
            kb_dir=self.kb_dir,
            vector_store_dir=v_store
        )
        self.assertGreater(len(account_chunks), 0)
        doc_titles = [c["doc_title"].lower() for c in account_chunks]
        self.assertTrue(any("account" in title for title in doc_titles), "Account FAQ should appear in top results")

        # Query 3: File Upload Limit
        tech_chunks = retrieve_relevant_chunks(
            query="What is the maximum file size limit for uploading a PDF document?",
            top_k=3,
            kb_dir=self.kb_dir,
            vector_store_dir=v_store
        )
        self.assertGreater(len(tech_chunks), 0)
        doc_titles = [c["doc_title"].lower() for c in tech_chunks]
        self.assertTrue(any("technical" in title for title in doc_titles), "Technical FAQ should appear in top results")

    def test_deterministic_sources_extraction(self):
        """Test extracting unique sources from chunk metadata."""
        sample_chunks = [
            {"doc_title": "Refund Policy", "section": "14-Day Guarantee"},
            {"doc_title": "Refund Policy", "section": "14-Day Guarantee"},
            {"doc_title": "Billing Policy", "section": "Accepted Methods"}
        ]
        sources = extract_deterministic_sources(sample_chunks)
        self.assertEqual(len(sources), 2)
        self.assertIn("Refund Policy (14-Day Guarantee)", sources)
        self.assertIn("Billing Policy (Accepted Methods)", sources)

    def test_database_rag_response_persistence(self):
        """Test storing and retrieving RAG response from SQLite."""
        db_path = str(self.temp_path / "test_p3.db")
        init_db(db_path)
        t_id = create_ticket("Jane Doe", "Refund issue", "Need refund", db_path=db_path)

        sources = ["Refund Policy (14-Day Guarantee)"]
        draft = "Hello Jane, we have processed your refund according to our 14-day policy."
        save_suggested_response(t_id, draft, sources, db_path=db_path)

        res = get_suggested_response(t_id, db_path=db_path)
        self.assertIsNotNone(res)
        self.assertEqual(res["suggested_response"], draft)
        self.assertEqual(res["retrieved_sources"], sources)


class TestLiveRAGGeneration(unittest.TestCase):
    """
    Optional live test for Gemini grounded response generation.
    Only executed when RUN_LIVE_GEMINI=1.
    """

    @unittest.skipUnless(
        os.getenv("RUN_LIVE_GEMINI") == "1",
        "Skipping live Gemini test by default. Set RUN_LIVE_GEMINI=1 to run."
    )
    def test_live_grounded_response_generation(self):
        self.assertTrue(is_gemini_configured(), "Gemini API key is not configured in .env")

        chunks = retrieve_relevant_chunks("How do I request a refund for an accidental duplicate charge?", top_k=2)
        success, response_text, sources = generate_suggested_response(
            customer_name="Alice Smith",
            subject="Duplicate Charge Refund",
            description="I was charged twice for this month's renewal. Can I get the extra charge refunded?",
            retrieved_chunks=chunks,
            category="Refund",
            priority="Medium"
        )
        self.assertTrue(success, f"Response generation failed: {response_text}")
        self.assertGreater(len(response_text), 30)
        self.assertGreater(len(sources), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
